"""Ordered independent watchlist aggregates using the accepted SQLite schema."""

from dataclasses import fields
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sqlite3

from stock_tracker.domain import DomainValidationError, Stock
from stock_tracker.exceptions import PersistenceDataError, PersistenceValidationError

from .connection import database_connection, transaction
from .migrations import ensure_schema, validate_schema
from .models import WatchlistEntry, WatchlistRecord


_METADATA = tuple(field.name for field in fields(WatchlistEntry))[4:]
_DECIMAL_TEXT = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_ENTRY_SELECT = (
    "SELECT ordinal, symbol, name, exchange, quantity, average_cost, current_price, "
    "sector, country, currency, market_cap, price_1d, price_5d, price_30d, price_3m, "
    "price_6m, price_1y, price_3y, price_5y FROM watchlist_entries "
    "WHERE namespace=? ORDER BY ordinal"
)
_ENTRY_INSERT = (
    "INSERT INTO watchlist_entries (namespace, ordinal, symbol, name, exchange, "
    "quantity, average_cost, current_price, sector, country, currency, market_cap, "
    "price_1d, price_5d, price_30d, price_3m, price_6m, price_1y, price_3y, price_5y) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


def _validate_namespace(namespace: str) -> None:
    if not isinstance(namespace, str) or not namespace.strip() or namespace != namespace.strip():
        raise PersistenceValidationError()
    _validate_text(namespace)


def _validate_text(value: str) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise PersistenceValidationError() from None


def _validated_record(record: WatchlistRecord) -> WatchlistRecord:
    """Copy/revalidate complete candidates, including deliberately mutated frozen records."""
    if not isinstance(record, WatchlistRecord) or not isinstance(getattr(record, "entries", None), tuple):
        raise PersistenceValidationError()
    entries = []
    try:
        for entry in record.entries:
            if not isinstance(entry, WatchlistEntry) or not isinstance(getattr(entry, "stock", None), Stock):
                raise PersistenceValidationError()
            stock = Stock(*(getattr(entry.stock, field, object()) for field in ("symbol", "name", "exchange")))
            entries.append(WatchlistEntry(
                stock, *(getattr(entry, field.name, object()) for field in fields(WatchlistEntry)[1:4]),
                *(getattr(entry, field, object()) for field in _METADATA),
            ))
        candidate = WatchlistRecord(getattr(record, "namespace", None),
                                   getattr(record, "name", None), tuple(entries))
        for value in (candidate.namespace, candidate.name):
            _validate_text(value)
        for entry in candidate.entries:
            for value in (entry.stock.symbol, entry.stock.name, entry.stock.exchange,
                          *(getattr(entry, field) for field in _METADATA)):
                if isinstance(value, str):
                    _validate_text(value)
        return candidate
    except (DomainValidationError, PersistenceValidationError):
        raise PersistenceValidationError() from None


def _decode_decimal(value: str | None, *, optional: bool = False) -> Decimal | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or _DECIMAL_TEXT.fullmatch(value) is None:
        raise PersistenceDataError()
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise PersistenceDataError() from None
    if not result.is_finite() or result < 0:
        raise PersistenceDataError()
    return result


def _read_watchlist(connection: sqlite3.Connection, namespace: str, name: str) -> WatchlistRecord:
    """Decode one complete aggregate on the caller's already validated snapshot."""
    entries = []
    try:
        for expected, row in enumerate(connection.execute(_ENTRY_SELECT, (namespace,))):
            ordinal, symbol, stock_name, exchange, quantity, cost, quote, *metadata = row
            if type(ordinal) is not int or ordinal != expected:
                raise PersistenceDataError()
            entries.append(WatchlistEntry(
                Stock(symbol, stock_name, exchange), _decode_decimal(quantity),
                _decode_decimal(cost, optional=True), _decode_decimal(quote, optional=True),
                *metadata,
            ))
        return WatchlistRecord(namespace, name, tuple(entries))
    except (DomainValidationError, PersistenceValidationError):
        raise PersistenceDataError() from None


def _write_watchlist(connection: sqlite3.Connection, record: WatchlistRecord) -> None:
    """Replace a validated aggregate in a caller-owned transaction; never commit."""
    connection.execute(
        "INSERT INTO watchlists(namespace, name) VALUES (?, ?) "
        "ON CONFLICT(namespace) DO UPDATE SET name=excluded.name",
        (record.namespace, record.name),
    )
    connection.execute("DELETE FROM watchlist_entries WHERE namespace=?", (record.namespace,))
    for ordinal, entry in enumerate(record.entries):
        connection.execute(_ENTRY_INSERT, (
            record.namespace, ordinal, entry.stock.symbol, entry.stock.name, entry.stock.exchange,
            str(entry.quantity), None if entry.average_cost is None else str(entry.average_cost),
            None if entry.current_price is None else str(entry.current_price),
            *(getattr(entry, field, object()) for field in _METADATA),
        ))


class SQLiteWatchlistRepository:
    """Fresh connections per operation; construction performs no filesystem/database IO."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path):
            raise PersistenceValidationError()
        self._path = path

    def get(self, namespace: str) -> WatchlistRecord | None:
        _validate_namespace(namespace)
        with database_connection(self._path) as connection:
            if connection is None:
                return None
            with transaction(connection):
                validate_schema(connection)
                parent = connection.execute(
                    "SELECT name FROM watchlists WHERE namespace=?", (namespace,),
                ).fetchone()
                if parent is None:
                    if connection.execute(
                        "SELECT 1 FROM watchlist_entries WHERE namespace=? LIMIT 1", (namespace,),
                    ).fetchone() is not None:
                        raise PersistenceDataError()
                    return None
                return _read_watchlist(connection, namespace, parent[0])

    def list(self) -> list[WatchlistRecord]:
        with database_connection(self._path) as connection:
            if connection is None:
                return []
            with transaction(connection):
                validate_schema(connection)
                if connection.execute(
                    "SELECT 1 FROM watchlist_entries AS e LEFT JOIN watchlists AS w "
                    "ON e.namespace=w.namespace WHERE w.namespace IS NULL LIMIT 1",
                ).fetchone() is not None:
                    raise PersistenceDataError()
                return [_read_watchlist(connection, namespace, name) for namespace, name in
                        connection.execute("SELECT namespace, name FROM watchlists ORDER BY namespace")]

    def save(self, record: WatchlistRecord) -> None:
        candidate = _validated_record(record)
        with database_connection(self._path, write=True) as connection:
            with transaction(connection, write=True):
                ensure_schema(connection)
                _write_watchlist(connection, candidate)
