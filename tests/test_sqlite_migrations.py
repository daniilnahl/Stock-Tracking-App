"""Temporary SQLite integration: exact schema, transaction ownership and refusal."""

from pathlib import Path
import sqlite3

import pytest


@pytest.fixture
def database(tmp_path):
    from stock_tracker.persistence.migrations import migrate_database

    path = tmp_path / "state.sqlite3"
    migrate_database(path)
    return path


def test_initialization_reopen_and_noop_preserve_rows_and_exact_schema(database):
    from stock_tracker.persistence.connection import database_connection, transaction
    from stock_tracker.persistence.migrations import migrate_database, validate_schema

    with database_connection(database, write=True) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert connection.execute("PRAGMA busy_timeout").fetchone() == (5000,)
        assert not connection.in_transaction
        with transaction(connection, write=True):
            connection.execute("INSERT INTO portfolios VALUES (?, ?)", ("-7", "Example"))
            connection.execute("INSERT INTO positions VALUES (?, ?, ?, ?, ?, ?, ?)",
                               ("-7", 0, "aapl", None, None, "0.2500", "1E+2"))
    before = database.read_bytes()
    migrate_database(database)
    assert database.read_bytes() == before
    with database_connection(database) as connection:
        with transaction(connection):
            validate_schema(connection)
            assert connection.execute("SELECT * FROM positions").fetchall() == [
                ("-7", 0, "aapl", None, None, "0.2500", "1E+2"),
            ]
            assert connection.execute("PRAGMA user_version").fetchone() == (1,)
            assert connection.execute("PRAGMA table_info(portfolios)").fetchall() == [
                (0, "id", "TEXT", 1, None, 1), (1, "name", "TEXT", 1, None, 0),
            ]
            entry_columns = connection.execute("PRAGMA table_info(watchlist_entries)").fetchall()
            assert [(row[1], row[2], row[3], row[5]) for row in entry_columns] == [
                ("namespace", "TEXT", 1, 1), ("ordinal", "INTEGER", 1, 2),
                ("symbol", "TEXT", 1, 0), ("name", "TEXT", 0, 0),
                ("exchange", "TEXT", 0, 0), ("quantity", "TEXT", 1, 0),
                ("average_cost", "TEXT", 0, 0), ("current_price", "TEXT", 0, 0),
                *[(name, "TEXT", 0, 0) for name in (
                    "sector", "country", "currency", "market_cap", "price_1d", "price_5d",
                    "price_30d", "price_3m", "price_6m", "price_1y", "price_3y", "price_5y",
                )],
            ]
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


@pytest.mark.parametrize("table,parent,parent_key,child_key", [
    ("positions", "portfolios", "id", "portfolio_id"),
    ("watchlist_entries", "watchlists", "namespace", "namespace"),
])
def test_both_child_foreign_keys_constraints_and_explicit_parent_cascade(
    database, table, parent, parent_key, child_key,
):
    from stock_tracker.persistence.connection import database_connection, transaction

    with database_connection(database, write=True) as connection:
        with transaction(connection, write=True):
            # Identifiers are fixed controlled test parameters; actual values bind.
            sql = f"INSERT INTO {table} ({child_key}, ordinal, symbol, quantity, average_cost) VALUES (?, ?, ?, ?, ?)"
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql, ("missing", 0, "AAPL", "0", "0"))
            connection.execute(f"INSERT INTO {parent} VALUES (?, ?)", ("key", "Example"))
            connection.execute(sql, ("key", 0, "AAPL", "0", "0"))
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql, ("key", 0, "MSFT", "0", "0"))
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql, ("key", -1, "MSFT", "0", "0"))
            connection.execute(f"DELETE FROM {parent} WHERE {parent_key} = ?", ("key",))
            assert connection.execute(f"SELECT * FROM {table}").fetchall() == []


@pytest.mark.parametrize("relative", [False, True])
def test_encoded_paths_spaces_hash_percent_unicode_and_read_is_readonly(tmp_path, relative):
    from stock_tracker.exceptions import PersistenceError
    from stock_tracker.persistence.connection import database_connection, transaction
    from stock_tracker.persistence.migrations import migrate_database, validate_schema

    name = "state space #100% é.sqlite3"
    path = Path(name) if relative else tmp_path / name
    migrate_database(path)
    assert (tmp_path / name).is_file()
    before = (tmp_path / name).read_bytes()
    with pytest.raises(PersistenceError) as caught:
        with database_connection(path) as connection:
            with transaction(connection):
                validate_schema(connection)
                connection.execute("INSERT INTO portfolios VALUES (?, ?)", ("1", "No write"))
    assert str(caught.value) == "Local storage operation failed."
    assert caught.value.__suppress_context__
    assert (tmp_path / name).read_bytes() == before


def test_missing_read_creates_no_file_or_parent_and_write_does_not_create_parent(tmp_path):
    from stock_tracker.exceptions import PersistenceError
    from stock_tracker.persistence.connection import database_connection
    from stock_tracker.persistence.migrations import migrate_database

    with database_connection(tmp_path / "absent.sqlite3") as connection:
        assert connection is None
    assert not (tmp_path / "absent.sqlite3").exists()
    path = tmp_path / "absent-parent" / "state.sqlite3"
    with pytest.raises(PersistenceError):
        with database_connection(path):
            pytest.fail("missing parent was accepted")
    assert not path.parent.exists()
    with pytest.raises(PersistenceError):
        migrate_database(path)
    assert not path.parent.exists()


@pytest.mark.parametrize("version", [-1, 2, 99])
def test_unsupported_version_refuses_read_and_migration_without_changes(tmp_path, version):
    from stock_tracker.exceptions import SchemaVersionError
    from stock_tracker.persistence.connection import database_connection, transaction
    from stock_tracker.persistence.migrations import migrate_database, validate_schema

    path = tmp_path / "future.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(f"PRAGMA user_version={version}")
        connection.execute("CREATE TABLE owner_data (data TEXT)")
        connection.execute("INSERT INTO owner_data VALUES (?)", ("preserve",))
    before = path.read_bytes()
    with pytest.raises(SchemaVersionError):
        migrate_database(path)
    with pytest.raises(SchemaVersionError):
        with database_connection(path) as connection:
            with transaction(connection):
                validate_schema(connection)
    assert path.read_bytes() == before


def test_unversioned_populated_and_corrupt_files_are_never_replaced(tmp_path):
    from stock_tracker.exceptions import PersistenceError, SchemaVersionError
    from stock_tracker.persistence.migrations import migrate_database

    populated = tmp_path / "old.sqlite3"
    with sqlite3.connect(populated) as connection:
        connection.execute("CREATE TABLE owner_data (data TEXT)")
        connection.execute("INSERT INTO owner_data VALUES (?)", ("preserve",))
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"synthetic invalid SQLite file")
    for path, error in ((populated, SchemaVersionError), (corrupt, PersistenceError)):
        before = path.read_bytes()
        with pytest.raises(error):
            migrate_database(path)
        assert path.read_bytes() == before


@pytest.mark.parametrize("change", [
    "missing_check", "weak_check", "real_quantity", "nullable_symbol", "wrong_pk",
    "wrong_fk", "no_cascade", "extra_table", "extra_index", "extra_trigger", "extra_view",
    "sqlite_prefix_lookalike", "merged_identifier",
])
def test_schema_tampering_is_refused_without_modification(tmp_path, change):
    from stock_tracker.exceptions import SchemaVersionError
    from stock_tracker.persistence.migrations import SCHEMA_V1, migrate_database

    path = tmp_path / "tampered.sqlite3"
    statements = dict(SCHEMA_V1)
    mutations = {
        "missing_check": ("positions", " CHECK (ordinal >= 0)", ""),
        "weak_check": ("watchlist_entries", "ordinal >= 0", "ordinal >= -1"),
        "real_quantity": ("positions", "quantity TEXT", "quantity REAL"),
        "nullable_symbol": ("watchlist_entries", "symbol TEXT NOT NULL", "symbol TEXT"),
        "wrong_pk": ("positions", "PRIMARY KEY (portfolio_id, ordinal)", "PRIMARY KEY (ordinal)"),
        "wrong_fk": ("positions", "REFERENCES portfolios(id)", "REFERENCES watchlists(namespace)"),
        "no_cascade": ("watchlist_entries", " ON DELETE CASCADE", ""),
        "merged_identifier": ("portfolios", "id TEXT", "idTEXT"),
    }
    if change in mutations:
        table, old, new = mutations[change]
        statements[table] = statements[table].replace(old, new)
    with sqlite3.connect(path) as connection:
        for statement in statements.values():
            connection.execute(statement)
        extras = {
            "extra_table": "CREATE TABLE extra (value TEXT)",
            "extra_index": "CREATE INDEX extra ON portfolios(name)",
            "extra_trigger": "CREATE TRIGGER extra AFTER INSERT ON portfolios BEGIN DELETE FROM portfolios; END",
            "extra_view": "CREATE VIEW extra AS SELECT * FROM portfolios",
            "sqlite_prefix_lookalike": "CREATE TABLE sqliteXhidden (value TEXT)",
        }
        if change in extras:
            connection.execute(extras[change])
        connection.execute("PRAGMA user_version=1")
    before = path.read_bytes()
    with pytest.raises(SchemaVersionError):
        migrate_database(path)
    assert path.read_bytes() == before


def test_empty_existing_file_initializes_and_formatting_case_changes_validate(tmp_path):
    from stock_tracker.persistence.migrations import SCHEMA_V1, migrate_database

    empty = tmp_path / "empty.sqlite3"
    empty.touch()
    migrate_database(empty)
    authored = tmp_path / "formatted.sqlite3"
    with sqlite3.connect(authored) as connection:
        for statement in SCHEMA_V1.values():
            connection.execute(statement.lower().replace("\n", " ") + ";")
        connection.execute("PRAGMA user_version=1")
    before = authored.read_bytes()
    migrate_database(authored)
    assert authored.read_bytes() == before


def test_mid_ddl_failure_rolls_back_schema_and_version_and_closes(monkeypatch, tmp_path):
    from stock_tracker.exceptions import PersistenceError
    from stock_tracker.persistence import connection as boundary
    from stock_tracker.persistence.migrations import migrate_database

    real_connect = sqlite3.connect
    opened = []

    class FailingConnection(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            if sql.startswith("CREATE TABLE positions"):
                raise sqlite3.OperationalError("synthetic-private-diagnostic")
            return super().execute(sql, parameters)

    def connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs, factory=FailingConnection)
        opened.append(connection)
        return connection

    monkeypatch.setattr(boundary.sqlite3, "connect", connect)
    path = tmp_path / "failure.sqlite3"
    with pytest.raises(PersistenceError) as caught:
        migrate_database(path)
    assert "synthetic-private" not in repr(caught.value)
    assert caught.value.__suppress_context__
    with pytest.raises(sqlite3.ProgrammingError):
        opened[0].execute("SELECT 1")
    with real_connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)
        assert connection.execute("SELECT name FROM sqlite_schema").fetchall() == []


def test_internal_steps_preserve_caller_transaction_and_rollback_schema_with_rows(tmp_path):
    from stock_tracker.exceptions import PersistenceValidationError
    from stock_tracker.persistence.connection import database_connection, transaction
    from stock_tracker.persistence.migrations import ensure_schema, validate_schema

    path = tmp_path / "import-later.sqlite3"
    with database_connection(path, write=True) as connection:
        with pytest.raises(PersistenceValidationError):
            ensure_schema(connection)
        with pytest.raises(RuntimeError, match="controlled"):
            with transaction(connection, write=True):
                ensure_schema(connection)
                validate_schema(connection)
                assert connection.in_transaction
                connection.execute("INSERT INTO portfolios VALUES (?, ?)", ("1", "Candidate"))
                raise RuntimeError("controlled")
        assert not connection.in_transaction
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)
        assert connection.execute("SELECT name FROM sqlite_schema").fetchall() == []
        with transaction(connection, write=True):
            ensure_schema(connection)
            with pytest.raises(PersistenceValidationError):
                with transaction(connection):
                    pytest.fail("nested transaction ran")
            assert connection.in_transaction


def test_failed_commit_rolls_back_owned_transaction_and_closes(monkeypatch, tmp_path):
    from stock_tracker.exceptions import PersistenceError
    from stock_tracker.persistence import connection as boundary
    from stock_tracker.persistence.migrations import ensure_schema

    real_connect = sqlite3.connect
    opened = []

    class FailingCommit(sqlite3.Connection):
        rolled_back = False
        closed = False

        def commit(self):
            raise sqlite3.OperationalError("synthetic-private-commit")

        def rollback(self):
            super().rollback()
            self.rolled_back = True

        def close(self):
            super().close()
            self.closed = True

    def connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs, factory=FailingCommit)
        opened.append(connection)
        return connection

    monkeypatch.setattr(boundary.sqlite3, "connect", connect)
    path = tmp_path / "commit-failure.sqlite3"
    with pytest.raises(PersistenceError) as caught:
        with boundary.database_connection(path, write=True) as connection:
            with boundary.transaction(connection, write=True):
                ensure_schema(connection)
                connection.execute("INSERT INTO portfolios VALUES (?, ?)", ("1", "Example"))
    assert str(caught.value) == "Local storage operation failed."
    assert caught.value.__suppress_context__
    assert opened[0].rolled_back and opened[0].closed
    with real_connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)
        assert connection.execute("SELECT name FROM sqlite_schema").fetchall() == []


def test_version_zero_read_requires_explicit_migration_without_changes(tmp_path):
    from stock_tracker.exceptions import SchemaVersionError
    from stock_tracker.persistence.connection import database_connection, transaction
    from stock_tracker.persistence.migrations import validate_schema

    path = tmp_path / "old-empty.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=0")
    before = path.read_bytes()
    with pytest.raises(SchemaVersionError):
        with database_connection(path) as connection:
            with transaction(connection):
                validate_schema(connection)
    assert path.read_bytes() == before


@pytest.mark.parametrize("failure", ["connect", "stat", "fk", "close"])
def test_connection_failures_are_sanitized_and_acquired_connections_closed(monkeypatch, tmp_path, failure):
    from stock_tracker.exceptions import PersistenceError
    from stock_tracker.persistence import connection as boundary

    real_connect = sqlite3.connect
    opened = []

    class ObservedConnection(sqlite3.Connection):
        closed = False

        def execute(self, sql, parameters=()):
            if failure == "fk" and sql == "PRAGMA foreign_keys=ON":
                return super().execute("SELECT 1")
            return super().execute(sql, parameters)

        def close(self):
            super().close()
            self.closed = True
            if failure == "close":
                raise sqlite3.OperationalError("synthetic-private-close")

    def connect(*args, **kwargs):
        if failure == "connect":
            raise sqlite3.OperationalError("synthetic-private-path")
        connection = real_connect(*args, **kwargs, factory=ObservedConnection)
        opened.append(connection)
        return connection

    monkeypatch.setattr(boundary.sqlite3, "connect", connect)
    if failure == "stat":
        monkeypatch.setattr(Path, "stat", lambda *a, **kw: (_ for _ in ()).throw(
            PermissionError("synthetic-private-path")))
    with pytest.raises(PersistenceError) as caught:
        with boundary.database_connection(tmp_path / "state.sqlite3", write=failure != "stat"):
            if failure != "close":
                pytest.fail("failed connection was yielded")
    assert str(caught.value) == "Local storage operation failed."
    assert "synthetic-private" not in repr(caught.value)
    assert caught.value.__suppress_context__
    assert all(connection.closed for connection in opened)
