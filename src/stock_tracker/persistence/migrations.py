"""One numbered schema runner; internal steps never commit a caller transaction."""

from pathlib import Path
import re
import sqlite3

from stock_tracker.exceptions import PersistenceValidationError, SchemaVersionError

from .connection import database_connection, transaction


CURRENT_VERSION = 1

# Static DDL contains no variable data. Execute each statement in the caller's
# transaction: executescript can implicitly commit pending work.
SCHEMA_V1 = {
    "portfolios": """CREATE TABLE portfolios (
        id TEXT PRIMARY KEY NOT NULL,
        name TEXT NOT NULL
    )""",
    "positions": """CREATE TABLE positions (
        portfolio_id TEXT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
        ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
        symbol TEXT NOT NULL,
        name TEXT,
        exchange TEXT,
        quantity TEXT NOT NULL,
        average_cost TEXT NOT NULL,
        PRIMARY KEY (portfolio_id, ordinal)
    )""",
    "watchlists": """CREATE TABLE watchlists (
        namespace TEXT PRIMARY KEY NOT NULL,
        name TEXT NOT NULL
    )""",
    "watchlist_entries": """CREATE TABLE watchlist_entries (
        namespace TEXT NOT NULL REFERENCES watchlists(namespace) ON DELETE CASCADE,
        ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
        symbol TEXT NOT NULL,
        name TEXT,
        exchange TEXT,
        quantity TEXT NOT NULL,
        average_cost TEXT,
        current_price TEXT,
        sector TEXT,
        country TEXT,
        currency TEXT,
        market_cap TEXT,
        price_1d TEXT,
        price_5d TEXT,
        price_30d TEXT,
        price_3m TEXT,
        price_6m TEXT,
        price_1y TEXT,
        price_3y TEXT,
        price_5y TEXT,
        PRIMARY KEY (namespace, ordinal)
    )""",
}


def _schema_objects(connection: sqlite3.Connection) -> list[tuple[str, str, str | None]]:
    return connection.execute(
        "SELECT type, name, sql FROM sqlite_schema "
        "WHERE substr(name, 1, 7) <> 'sqlite_' ORDER BY name"
    ).fetchall()


def _normalized(sql: str) -> tuple[str, ...]:
    # V1 has no quoted identifiers or string literals. Canonical DDL comparison
    # preserves operators and types while accepting formatting/case differences.
    tokens = re.findall(r"[A-Za-z_][A-Za-z_0-9]*|\d+|>=|<=|<>|!=|[^\s]", sql.casefold())
    if tokens and tokens[-1] == ";":
        tokens.pop()
    return tuple(tokens)


def _require_transaction(connection: sqlite3.Connection) -> None:
    if not connection.in_transaction:
        raise PersistenceValidationError()
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise PersistenceValidationError()


def validate_schema(connection: sqlite3.Connection) -> None:
    """Validate exact version-1 DDL in the caller's stable snapshot.

    Matching complete canonical table definitions verifies columns, types,
    nullability, keys, ordinal checks and foreign-key/cascade declarations;
    unknown objects and independently authored alternative DDL are unsupported.
    This does not validate stored domain records, which repositories must decode.
    """
    _require_transaction(connection)
    if connection.execute("PRAGMA user_version").fetchone() != (CURRENT_VERSION,):
        raise SchemaVersionError()
    objects = _schema_objects(connection)
    if len(objects) != len(SCHEMA_V1):
        raise SchemaVersionError()
    for kind, name, sql in objects:
        if (kind != "table" or name not in SCHEMA_V1 or sql is None
                or _normalized(sql) != _normalized(SCHEMA_V1[name])):
            raise SchemaVersionError()


def _migration_1(connection: sqlite3.Connection) -> None:
    for statement in SCHEMA_V1.values():
        connection.execute(statement)
    connection.execute("PRAGMA user_version=1")


def ensure_schema(connection: sqlite3.Connection) -> None:
    """Apply numbered migration 1 or validate v1 without committing caller work.

    Import/repository writers must call this inside their existing write
    transaction so schema/version and their records roll back together.
    """
    _require_transaction(connection)
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        if _schema_objects(connection):
            raise SchemaVersionError()
        _migration_1(connection)
    elif version != CURRENT_VERSION:
        raise SchemaVersionError()
    validate_schema(connection)


def migrate_database(path: Path) -> None:
    """Explicitly initialize a new/empty v0 database or validate an existing v1.

    A future upgrade of an existing schema requires verified backup first; no
    such upgrade is introduced here. Failed creation may leave an empty file.
    """
    with database_connection(path, write=True) as connection:
        with transaction(connection, write=True):
            ensure_schema(connection)
