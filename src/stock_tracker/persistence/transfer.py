"""Strict neutral JSON import and checked SQLite copies; never deserialize pickle."""

from contextlib import contextmanager
from dataclasses import fields
from decimal import Decimal
import json
import os
from pathlib import Path
import sqlite3

from stock_tracker.domain import DomainValidationError, Portfolio, Position, Stock
from stock_tracker.exceptions import (
    PersistenceConflictError, PersistenceDataError, PersistenceError,
    PersistenceValidationError,
)

from .connection import database_connection, transaction
from .migrations import ensure_schema, validate_schema
from .models import WatchlistEntry, WatchlistRecord
from .sqlite_portfolios import (
    _create_portfolio, _decode_decimal, _decode_id, _encode_id,
    _list_portfolios, _validated_portfolio,
)
from .sqlite_watchlists import _read_watchlist, _validated_record, _write_watchlist


MAX_BYTES = 10 * 1024 * 1024
MAX_AGGREGATES = 10_000
MAX_ENTRIES = 100_000
MAX_DEPTH = 64
MAX_STRING = 4096
_ENTRY_FIELDS = tuple(field.name for field in fields(WatchlistEntry))


def _paths(source: Path, destination: Path) -> tuple[Path, Path]:
    if not isinstance(source, Path) or not isinstance(destination, Path):
        raise PersistenceValidationError()
    try:
        source, destination = source.resolve(), destination.resolve()
        source_state = source.stat()
        try:
            destination_state = destination.stat()
        except FileNotFoundError:
            destination_state = None
        if source == destination or (destination_state is not None and
                                     os.path.samestat(source_state, destination_state)):
            raise PersistenceValidationError()
        return source, destination
    except OSError:
        raise PersistenceError() from None
    except RuntimeError:
        # Path.resolve reports symlink loops as RuntimeError on Python 3.11.
        raise PersistenceError() from None


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise PersistenceValidationError()
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PersistenceValidationError()


def _check_depth(text: str) -> None:
    depth = 0
    quoted = escaped = False
    for character in text:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise PersistenceValidationError()
        elif character in "]}":
            depth -= 1


def _check_strings(value: object) -> None:
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            if len(item) > MAX_STRING:
                raise PersistenceValidationError()
            try:
                item.encode("utf-8")
            except UnicodeError:
                raise PersistenceValidationError() from None
        elif isinstance(item, dict):
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)


def _object(value: object, keys: tuple[str, ...]) -> dict:
    if not isinstance(value, dict) or set(value) != set(keys):
        raise PersistenceValidationError()
    return value


def _array(value: object) -> list:
    if not isinstance(value, list):
        raise PersistenceValidationError()
    return value


def _stock(value: object) -> Stock:
    item = _object(value, ("symbol", "name", "exchange"))
    return Stock(**item)


def _decimal(value: object, *, optional: bool = False) -> Decimal | None:
    return None if optional and value is None else _decode_decimal(value)


def _read_neutral(source: Path) -> tuple[list[Portfolio], list[WatchlistRecord]]:
    try:
        with source.open("rb") as stream:
            content = stream.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise PersistenceValidationError()
        text = content.decode("utf-8")
        _check_depth(text)
        payload = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        _check_strings(payload)
        root = _object(payload, ("format", "version", "portfolios", "watchlists"))
        if root["format"] != "stock-tracker-neutral" or type(root["version"]) is not int or root["version"] != 1:
            raise PersistenceValidationError()
        portfolios, watchlists = _array(root["portfolios"]), _array(root["watchlists"])
        if len(portfolios) + len(watchlists) > MAX_AGGREGATES:
            raise PersistenceValidationError()
        entry_count = 0
        for item in portfolios:
            _object(item, ("id", "name", "positions"))
            entry_count += len(_array(item["positions"]))
        for item in watchlists:
            _object(item, ("namespace", "name", "entries"))
            entry_count += len(_array(item["entries"]))
        if entry_count > MAX_ENTRIES:
            raise PersistenceValidationError()
        decoded_portfolios, decoded_watchlists = [], []
        ids, namespaces = set(), set()
        for item in portfolios:
            portfolio_id = None if item["id"] is None else _decode_id(item["id"])
            if portfolio_id is not None:
                if portfolio_id in ids:
                    raise PersistenceValidationError()
                ids.add(portfolio_id)
            positions = []
            for position in item["positions"]:
                _object(position, ("stock", "quantity", "average_cost"))
                positions.append(Position(_stock(position["stock"]), _decimal(position["quantity"]),
                                          _decimal(position["average_cost"])))
            decoded_portfolios.append(_validated_portfolio(Portfolio(portfolio_id, item["name"], positions)))
        for item in watchlists:
            entries = []
            for entry in item["entries"]:
                _object(entry, _ENTRY_FIELDS)
                entries.append(WatchlistEntry(
                    _stock(entry["stock"]), _decimal(entry["quantity"]),
                    _decimal(entry["average_cost"], optional=True),
                    _decimal(entry["current_price"], optional=True),
                    *(entry[field] for field in _ENTRY_FIELDS[4:]),
                ))
            record = _validated_record(WatchlistRecord(item["namespace"], item["name"], tuple(entries)))
            if record.namespace in namespaces:
                raise PersistenceValidationError()
            namespaces.add(record.namespace)
            decoded_watchlists.append(record)
        return decoded_portfolios, decoded_watchlists
    except OSError:
        raise PersistenceError() from None
    except (UnicodeError, ValueError, RecursionError, DomainValidationError, PersistenceDataError):
        raise PersistenceValidationError() from None


def import_neutral_state(source: Path, destination: Path) -> None:
    """Add fully reviewed neutral records atomically, refusing all collisions."""
    source, destination = _paths(source, destination)
    portfolios, watchlists = _read_neutral(source)
    with database_connection(destination, write=True) as connection:
        with transaction(connection, write=True):
            ensure_schema(connection)
            _validate_database(connection)
            for portfolio in portfolios:
                if portfolio.id is not None and connection.execute(
                    "SELECT 1 FROM portfolios WHERE id=?", (_encode_id(portfolio.id),),
                ).fetchone():
                    raise PersistenceConflictError()
            for record in watchlists:
                if connection.execute("SELECT 1 FROM watchlists WHERE namespace=?", (record.namespace,)).fetchone():
                    raise PersistenceConflictError()
            # Explicit IDs are reserved by inserting them before any allocation.
            for portfolio in portfolios:
                if portfolio.id is not None:
                    _create_portfolio(connection, portfolio)
            for portfolio in portfolios:
                if portfolio.id is None:
                    _create_portfolio(connection, portfolio)
            for record in watchlists:
                _write_watchlist(connection, record)


def _validate_database(connection: sqlite3.Connection) -> None:
    validate_schema(connection)
    if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise PersistenceDataError()
    if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise PersistenceDataError()
    _list_portfolios(connection)
    for namespace, name in connection.execute("SELECT namespace, name FROM watchlists ORDER BY namespace"):
        _read_watchlist(connection, namespace, name)


@contextmanager
def _reserve(destination: Path):
    try:
        # O_EXCL prevents replacing a file created since the initial path check.
        with destination.open("xb") as reserved:
            yield reserved
    except FileExistsError:
        raise PersistenceConflictError() from None
    except OSError:
        raise PersistenceError() from None


@contextmanager
def _copy_connection(destination: Path, reserved):
    connection = None
    try:
        try:
            # Verify the reserved identity around opening; never recreate a removed file.
            if not os.path.samestat(os.fstat(reserved.fileno()), destination.stat()):
                raise PersistenceConflictError()
            connection = sqlite3.connect(destination.as_uri() + "?mode=rw", uri=True,
                                         timeout=5.0, isolation_level=None)
            if not os.path.samestat(os.fstat(reserved.fileno()), destination.stat()):
                raise PersistenceConflictError()
            connection.execute("PRAGMA foreign_keys=ON")
            if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
                raise PersistenceError() from None
            yield connection
        finally:
            if connection is not None:
                connection.close()
    except (sqlite3.Error, OSError):
        raise PersistenceError() from None


def _checked_copy(source: Path, destination: Path) -> None:
    requested_destination = destination
    source, destination = _paths(source, destination)
    try:
        requested_destination.lstat()
    except FileNotFoundError:
        pass
    except OSError:
        raise PersistenceError() from None
    else:
        # An occupied directory entry includes a dangling symlink.
        raise PersistenceConflictError()
    with database_connection(source) as original:
        if original is None:
            raise PersistenceError()
        with transaction(original):
            _validate_database(original)
            with _reserve(destination) as reserved:
                with _copy_connection(destination, reserved) as copied:
                    original.backup(copied)
                    with transaction(copied):
                        _validate_database(copied)


def backup_database(source: Path, destination: Path) -> None:
    """Make a validated consistent SQLite snapshot into an exclusively new file."""
    _checked_copy(source, destination)


def restore_database(source: Path, destination: Path) -> None:
    """Copy a verified backup to a new destination; never replace active state."""
    _checked_copy(source, destination)
