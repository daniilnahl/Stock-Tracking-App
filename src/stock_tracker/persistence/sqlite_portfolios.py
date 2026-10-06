"""Exact Portfolio mapping and atomic, short-lived SQLite repositories."""

from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sqlite3

from stock_tracker.domain import DomainValidationError, Portfolio, Position, Stock
from stock_tracker.exceptions import (
    PersistenceConflictError, PersistenceDataError, PersistenceNotFoundError,
    PersistenceValidationError,
)

from .connection import database_connection, transaction
from .migrations import ensure_schema, validate_schema


_INTEGER = re.compile(r"(?:0|[1-9][0-9]*|-[1-9][0-9]*)\Z")
_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


def _encode_id(value: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PersistenceValidationError()
    return format(Decimal(value), "f")


def _decode_id(value: object) -> int:
    if not isinstance(value, str) or _INTEGER.fullmatch(value) is None:
        raise PersistenceDataError()
    return int(Decimal(value))


def _decode_decimal(value: object) -> Decimal:
    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        raise PersistenceDataError()
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise PersistenceDataError() from None
    if not result.is_finite() or result < 0:
        raise PersistenceDataError()
    return result


def _validated_portfolio(candidate: Portfolio) -> Portfolio:
    """Copy/revalidate mutable and bypass-mutated domain inputs before any IO."""
    if not isinstance(candidate, Portfolio) or not isinstance(getattr(candidate, "positions", None), list):
        raise PersistenceValidationError()
    try:
        positions = []
        for position in candidate.positions:
            if not isinstance(position, Position) or not isinstance(getattr(position, "stock", None), Stock):
                raise PersistenceValidationError()
            missing = object()
            stock = Stock(getattr(position.stock, "symbol", missing),
                          getattr(position.stock, "name", missing),
                          getattr(position.stock, "exchange", missing))
            positions.append(Position(stock, getattr(position, "quantity", missing),
                                      getattr(position, "average_cost", missing)))
        result = Portfolio(getattr(candidate, "id", object()), getattr(candidate, "name", None), positions)
    except DomainValidationError:
        raise PersistenceValidationError() from None
    # Domain strings are Unicode; SQLite binds UTF-8 text. Reject values it
    # cannot represent before opening/creating storage, without replacement.
    try:
        result.name.encode("utf-8")
        for position in result.positions:
            for value in (position.stock.symbol, position.stock.name, position.stock.exchange):
                if value is not None:
                    value.encode("utf-8")
    except UnicodeError:
        raise PersistenceValidationError() from None
    return result


def _read_portfolio(connection: sqlite3.Connection, row: tuple) -> Portfolio:
    """Decode a complete aggregate inside the caller's schema-validated snapshot."""
    encoded_id, name = row
    portfolio_id = _decode_id(encoded_id)
    children = connection.execute(
        "SELECT ordinal, symbol, name, exchange, quantity, average_cost FROM positions "
        "WHERE portfolio_id=? ORDER BY ordinal", (encoded_id,),
    ).fetchall()
    positions = []
    try:
        for expected, (ordinal, symbol, stock_name, exchange, quantity, cost) in enumerate(children):
            if type(ordinal) is not int or ordinal != expected:
                raise PersistenceDataError()
            positions.append(Position(
                Stock(symbol, stock_name, exchange),
                _decode_decimal(quantity), _decode_decimal(cost),
            ))
        return Portfolio(portfolio_id, name, positions)
    except DomainValidationError:
        raise PersistenceDataError() from None


def _list_portfolios(connection: sqlite3.Connection) -> list[Portfolio]:
    if connection.execute(
        "SELECT 1 FROM positions LEFT JOIN portfolios ON positions.portfolio_id=portfolios.id "
        "WHERE portfolios.id IS NULL LIMIT 1"
    ).fetchone():
        raise PersistenceDataError()
    rows = connection.execute("SELECT id, name FROM portfolios").fetchall()
    return sorted((_read_portfolio(connection, row) for row in rows), key=lambda item: item.id)


def _allocate_id(connection: sqlite3.Connection) -> int:
    ids = [_decode_id(row[0]) for row in connection.execute("SELECT id FROM portfolios")]
    return max([0, *ids]) + 1


def _insert_positions(connection: sqlite3.Connection, portfolio: Portfolio) -> None:
    encoded_id = _encode_id(portfolio.id)
    connection.executemany(
        "INSERT INTO positions (portfolio_id, ordinal, symbol, name, exchange, quantity, "
        "average_cost) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(encoded_id, ordinal, position.stock.symbol, position.stock.name,
          position.stock.exchange, str(position.quantity), str(position.average_cost))
         for ordinal, position in enumerate(portfolio.positions)],
    )


def _create_portfolio(connection: sqlite3.Connection, portfolio: Portfolio) -> Portfolio:
    """Insert validated input on a caller-owned transaction; never commit here."""
    portfolio_id = _allocate_id(connection) if portfolio.id is None else portfolio.id
    encoded_id = _encode_id(portfolio_id)
    if connection.execute("SELECT 1 FROM portfolios WHERE id=?", (encoded_id,)).fetchone():
        raise PersistenceConflictError()
    result = Portfolio(portfolio_id, portfolio.name, portfolio.positions)
    connection.execute("INSERT INTO portfolios (id, name) VALUES (?, ?)",
                       (encoded_id, result.name))
    _insert_positions(connection, result)
    return result


class SQLitePortfolioRepository:
    """Preserve exact Portfolio inputs; construction performs no storage IO."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path):
            raise PersistenceValidationError()
        self._path = path

    def create(self, portfolio: Portfolio) -> Portfolio:
        candidate = _validated_portfolio(portfolio)
        with database_connection(self._path, write=True) as connection:
            with transaction(connection, write=True):
                ensure_schema(connection)
                return _create_portfolio(connection, candidate)

    def get(self, portfolio_id: int) -> Portfolio | None:
        encoded_id = _encode_id(portfolio_id)
        with database_connection(self._path) as connection:
            if connection is None:
                return None
            with transaction(connection):
                validate_schema(connection)
                row = connection.execute("SELECT id, name FROM portfolios WHERE id=?",
                                         (encoded_id,)).fetchone()
                if row is None and connection.execute(
                    "SELECT 1 FROM positions WHERE portfolio_id=? LIMIT 1", (encoded_id,),
                ).fetchone():
                    raise PersistenceDataError()
                return None if row is None else _read_portfolio(connection, row)

    def list(self) -> list[Portfolio]:
        with database_connection(self._path) as connection:
            if connection is None:
                return []
            with transaction(connection):
                validate_schema(connection)
                return _list_portfolios(connection)

    def save(self, portfolio: Portfolio) -> None:
        candidate = _validated_portfolio(portfolio)
        if candidate.id is None:
            raise PersistenceNotFoundError()
        encoded_id = _encode_id(candidate.id)
        with database_connection(self._path, write=True) as connection:
            with transaction(connection, write=True):
                ensure_schema(connection)
                if not connection.execute("SELECT 1 FROM portfolios WHERE id=?",
                                          (encoded_id,)).fetchone():
                    raise PersistenceNotFoundError()
                connection.execute("UPDATE portfolios SET name=? WHERE id=?",
                                   (candidate.name, encoded_id))
                connection.execute("DELETE FROM positions WHERE portfolio_id=?", (encoded_id,))
                _insert_positions(connection, candidate)

    def delete(self, portfolio_id: int) -> bool:
        encoded_id = _encode_id(portfolio_id)
        # Absence is a read and must not initialize a database.
        with database_connection(self._path) as connection:
            if connection is None:
                return False
        with database_connection(self._path, write=True) as connection:
            with transaction(connection, write=True):
                ensure_schema(connection)
                cursor = connection.execute("DELETE FROM portfolios WHERE id=?", (encoded_id,))
                return cursor.rowcount == 1
