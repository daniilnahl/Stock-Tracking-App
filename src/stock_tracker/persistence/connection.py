"""Explicit, short-lived SQLite connections and caller-owned transactions."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

from stock_tracker.exceptions import PersistenceError, PersistenceValidationError


@contextmanager
def database_connection(path: Path, *, write: bool = False) -> Iterator[sqlite3.Connection | None]:
    """Open an encoded SQLite URI; a missing read returns None without creating state.

    Connections use explicit transactions, the default five-second lock timeout,
    and enforced foreign keys. This boundary sanitizes storage failures from the
    operation as well as opening/closing; programming exceptions propagate.
    """
    if not isinstance(path, Path) or not isinstance(write, bool):
        raise PersistenceValidationError()
    connection = None
    try:
        try:
            if not write:
                try:
                    path.stat()
                except FileNotFoundError:
                    # A missing database in an existing directory is absence;
                    # a missing parent is a configuration/filesystem failure.
                    path.parent.stat()
                    yield None
                    return
            uri = path.resolve().as_uri() + ("?mode=rwc" if write else "?mode=ro")
            connection = sqlite3.connect(uri, uri=True, timeout=5.0, isolation_level=None)
            connection.execute("PRAGMA foreign_keys=ON")
            if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
                raise PersistenceError() from None
            yield connection
        finally:
            if connection is not None:
                connection.close()
    except (sqlite3.Error, OSError):
        raise PersistenceError() from None


@contextmanager
def transaction(connection: sqlite3.Connection, *, write: bool = False) -> Iterator[None]:
    """Own one snapshot/write transaction; never nest or commit a caller's work."""
    if connection.in_transaction or not isinstance(write, bool):
        raise PersistenceValidationError()
    connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
    try:
        yield
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
