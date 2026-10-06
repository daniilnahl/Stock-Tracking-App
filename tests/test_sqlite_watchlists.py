"""Watchlist persistence against real isolated SQLite and root facade objects."""

from dataclasses import fields
from decimal import Decimal
from pathlib import Path
import sqlite3

import pytest


@pytest.fixture
def entry():
    from stock_tracker.domain import Stock
    from stock_tracker.persistence.models import WatchlistEntry
    return WatchlistEntry(Stock("a'\"APL", name="Example", exchange="NASDAQ"), Decimal("0.2500"),
                          Decimal("100.123456789012345678901234567890"), Decimal("0.00"),
                          "Tech", None, "USD", "1.000B", "", "N/A", "-", "1.20", None,
                          "0", "8", "9")


def record(namespace, entries=(), name="Example"):
    from stock_tracker.persistence.models import WatchlistRecord
    return WatchlistRecord(namespace, name, tuple(entries))


def assert_entries(actual, expected):
    for found, wanted in zip(actual.entries, expected.entries, strict=True):
        assert (found.stock.symbol, found.stock.name, found.stock.exchange) == (
            wanted.stock.symbol, wanted.stock.name, wanted.stock.exchange,
        )
        for field in fields(found):
            if field.name == "stock":
                continue
            left, right = getattr(found, field.name), getattr(wanted, field.name)
            assert left == right
            if isinstance(right, Decimal):
                assert left.as_tuple() == right.as_tuple()


def test_round_trip_order_duplicates_namespaces_exact_precision(tmp_path, entry):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.persistence.models import WatchlistEntry
    from stock_tracker.domain import Stock
    path = tmp_path / "special #% name.sqlite3"
    unowned = WatchlistEntry(Stock("a'\"APL"), Decimal("-0.000"), None, None,
                            *(None for _ in range(12)))
    zero = WatchlistEntry(Stock("ZERO"), Decimal("0"), Decimal("0"), Decimal("0"),
                         *(None for _ in range(12)))
    first = record("menu_watchlist", [entry, entry, unowned, zero])
    second = record("daniils_stock_method", [], "Other")
    repo = SQLiteWatchlistRepository(path)
    repo.save(first)
    repo.save(second)
    reopened = SQLiteWatchlistRepository(path)
    assert_entries(reopened.get(first.namespace), first)
    assert reopened.get(second.namespace).entries == ()
    assert [r.namespace for r in reopened.list()] == [second.namespace, first.namespace]
    repo.save(record(first.namespace, [zero], "Changed"))
    assert reopened.get(first.namespace).name == "Changed"
    assert len(reopened.get(first.namespace).entries) == 1
    assert reopened.get(second.namespace).name == "Other"
    repo.save(record("Menu_watchlist", [], "Case distinct"))
    assert len(repo.list()) == 3
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM portfolios").fetchone() == (0,)
        assert connection.execute("SELECT quantity, average_cost, current_price FROM watchlist_entries").fetchone() == ("0", "0", "0")


def test_construction_and_missing_reads_do_not_create_state(tmp_path, monkeypatch):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceError
    path = tmp_path / "missing.sqlite3"
    with monkeypatch.context() as guards:
        guards.setattr(sqlite3, "connect", lambda *args, **kwargs: pytest.fail("constructor IO"))
        guards.setattr(Path, "stat", lambda *args: pytest.fail("constructor IO"))
        repo = SQLiteWatchlistRepository(path)
    assert repo.get("menu_watchlist") is None
    assert repo.list() == []
    assert not path.exists()
    absent = SQLiteWatchlistRepository(tmp_path / "missing-parent" / "state.sqlite3")
    for operation in (lambda: absent.get("menu_watchlist"), absent.list,
                      lambda: absent.save(record("menu_watchlist"))):
        with pytest.raises(PersistenceError) as caught:
            operation()
        assert str(caught.value) == "Local storage operation failed."
        assert caught.value.__suppress_context__
    assert not absent._path.parent.exists()


@pytest.mark.parametrize("invalid", [None, True, 1, "", " ", " menu", "menu "])
def test_invalid_namespace_precedes_io(tmp_path, monkeypatch, invalid):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceValidationError
    repo = SQLiteWatchlistRepository(tmp_path / "absent.sqlite3")
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: pytest.fail("invalid input IO"))
    with pytest.raises(PersistenceValidationError):
        repo.get(invalid)


@pytest.mark.parametrize("field,value", [
    ("quantity", True), ("quantity", "1"), ("quantity", Decimal("NaN")),
    ("quantity", Decimal("-1")), ("average_cost", Decimal("Infinity")),
    ("average_cost", None), ("current_price", Decimal("-1")),
    ("country", 1), ("price_5y", False), ("stock", object()),
])
def test_mutated_entry_rejected_before_io(tmp_path, monkeypatch, entry, field, value):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceValidationError
    object.__setattr__(entry, field, value)
    candidate = record("menu_watchlist", [entry])
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: pytest.fail("invalid input IO"))
    with pytest.raises(PersistenceValidationError):
        SQLiteWatchlistRepository(tmp_path / "absent.sqlite3").save(candidate)


@pytest.mark.parametrize("field,value", [("namespace", "bad "), ("name", ""), ("entries", []),
                                         ("entries", (object(),))])
def test_mutated_record_rejected_before_io(tmp_path, monkeypatch, field, value):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceValidationError
    candidate = record("menu_watchlist")
    object.__setattr__(candidate, field, value)
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: pytest.fail("invalid input IO"))
    with pytest.raises(PersistenceValidationError):
        SQLiteWatchlistRepository(tmp_path / "absent.sqlite3").save(candidate)


def test_mutated_identity_rejected_before_io(tmp_path, monkeypatch, entry):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceValidationError
    object.__setattr__(entry.stock, "symbol", " bad ")
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: pytest.fail("invalid input IO"))
    with pytest.raises(PersistenceValidationError):
        SQLiteWatchlistRepository(tmp_path / "absent.sqlite3").save(record("menu", [entry]))


@pytest.mark.parametrize("column,value", [
    ("quantity", "NaN"), ("quantity", "1_0"), ("quantity", " 1"),
    ("quantity", "-1"), ("average_cost", None), ("current_price", "Infinity"),
    ("symbol", " bad "), ("name", ""), ("exchange", " "),
    ("sector", b"invalid-blob"), ("ordinal", 2), ("ordinal", 0.5),
])
def test_corrupt_row_rejects_whole_get_and_list(tmp_path, entry, column, value):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceDataError
    path = tmp_path / "state.sqlite3"
    repo = SQLiteWatchlistRepository(path)
    repo.save(record("a-valid", [entry]))
    repo.save(record("z-bad", [entry]))
    # The identifier comes only from this fixed test matrix; row values are bound.
    with sqlite3.connect(path) as connection:
        connection.execute(f"UPDATE watchlist_entries SET {column}=? WHERE namespace=?", (value, "z-bad"))
    before = path.read_bytes()
    for operation in (lambda: repo.get("z-bad"), repo.list):
        with pytest.raises(PersistenceDataError) as caught:
            operation()
        assert str(caught.value) == "Local storage data is invalid."
    assert path.read_bytes() == before
    assert repo.get("a-valid").name == "Example"


@pytest.mark.parametrize("column,value", [("name", " bad "), ("namespace", " bad ")])
def test_corrupt_parent_rejects_list(tmp_path, column, value):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceDataError
    repo = SQLiteWatchlistRepository(tmp_path / "state.sqlite3")
    repo.save(record("menu"))
    with sqlite3.connect(repo._path) as connection:
        connection.execute(f"UPDATE watchlists SET {column}=?", (value,))
    with pytest.raises(PersistenceDataError):
        repo.list()


def test_orphan_rows_are_not_silently_ignored(tmp_path, entry):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceDataError
    repo = SQLiteWatchlistRepository(tmp_path / "state.sqlite3")
    repo.save(record("menu", [entry]))
    with sqlite3.connect(repo._path) as connection:
        connection.execute("DELETE FROM watchlists")
    with pytest.raises(PersistenceDataError):
        repo.get("menu")
    with pytest.raises(PersistenceDataError):
        repo.list()


def test_failed_replacement_rolls_back_parent_and_children(tmp_path, monkeypatch, entry):
    from stock_tracker.persistence import sqlite_watchlists as module
    from stock_tracker.exceptions import PersistenceError
    repo = module.SQLiteWatchlistRepository(tmp_path / "state.sqlite3")
    original = record("menu", [entry, entry])
    repo.save(original)
    repo.save(record("other"))
    actual_write = module._write_watchlist
    def fail_after_replace(connection, candidate):
        actual_write(connection, candidate)
        raise sqlite3.OperationalError("private path/value must never escape")
    with monkeypatch.context() as guards:
        guards.setattr(module, "_write_watchlist", fail_after_replace)
        with pytest.raises(PersistenceError) as caught:
            repo.save(record("menu", [], "Changed"))
    assert str(caught.value) == "Local storage operation failed."
    assert caught.value.__suppress_context__
    assert repo.get("menu").name == original.name
    assert_entries(repo.get("menu"), original)
    assert len(repo.list()) == 2


def test_initialization_and_rows_rollback_together(tmp_path, monkeypatch, entry):
    from stock_tracker.persistence import sqlite_watchlists as module
    from stock_tracker.exceptions import PersistenceError
    path = tmp_path / "state.sqlite3"
    actual_write = module._write_watchlist
    def fail(connection, candidate):
        actual_write(connection, candidate)
        raise sqlite3.OperationalError("failure")
    monkeypatch.setattr(module, "_write_watchlist", fail)
    with pytest.raises(PersistenceError):
        module.SQLiteWatchlistRepository(path).save(record("menu", [entry]))
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)
        assert connection.execute("SELECT name FROM sqlite_schema WHERE type='table'").fetchall() == []


@pytest.mark.parametrize("kind", ["future", "corrupt", "unversioned"])
def test_unsupported_state_refused_without_changes(tmp_path, kind):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceError, SchemaVersionError
    path = tmp_path / "state.sqlite3"
    if kind == "corrupt":
        path.write_bytes(b"not sqlite")
    else:
        with sqlite3.connect(path) as connection:
            connection.execute("PRAGMA user_version=9" if kind == "future" else "CREATE TABLE other(x)")
    before = path.read_bytes()
    repo = SQLiteWatchlistRepository(path)
    error = PersistenceError if kind == "corrupt" else SchemaVersionError
    for operation in (repo.list, lambda: repo.get("menu"), lambda: repo.save(record("menu"))):
        with pytest.raises(error):
            operation()
        assert path.read_bytes() == before


def test_read_schema_parent_children_share_transaction_and_connections_close(tmp_path, monkeypatch, entry):
    from stock_tracker.persistence import connection as boundary
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    repo = SQLiteWatchlistRepository(tmp_path / "state.sqlite3")
    repo.save(record("menu", [entry]))
    events = []
    actual_connect = sqlite3.connect
    class TrackedConnection(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            events.append((sql, self.in_transaction))
            return super().execute(sql, parameters)
        def close(self):
            events.append(("CLOSE", self.in_transaction))
            return super().close()
    monkeypatch.setattr(boundary.sqlite3, "connect", lambda *args, **kwargs:
                        actual_connect(*args, **kwargs, factory=TrackedConnection))
    for operation in (lambda: repo.get("menu"), repo.list):
        events.clear()
        operation()
        selects = [(sql, active) for sql, active in events if sql.startswith("SELECT")]
        assert selects and all(active for _, active in selects)
        assert events[-1] == ("CLOSE", False)
    events.clear()
    repo.save(record("menu", [entry]))
    assert ("BEGIN IMMEDIATE", False) in events
    assert events[-1] == ("CLOSE", False)


def test_facade_round_trip_recomputes_without_provider_config_or_saved_keys(tmp_path, monkeypatch):
    from stock import Stock
    from watch_list import Watch_list
    from stock_tracker.compatibility.watchlist_persistence import record_to_watchlist, watchlist_to_record
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.compatibility import stock_operations
    import config
    import stock as stock_module
    def denied(*args, **kwargs):
        pytest.fail("restoration fetched runtime configuration or provider")
    monkeypatch.setattr(config, "load_configuration", denied)
    monkeypatch.setattr(stock_module, "load_configuration", denied)
    monkeypatch.setattr(stock_operations.provider_factory, "create_market_data_provider", denied)
    old_key = "fictional-old-runtime"
    current_key = "fictional-current-runtime"
    owned = Stock("ABC", old_key, name="Example", exchange="NASDAQ", amount_owned="0.2500",
                  cost_basis="100.0000", current_price="120.0000", total_return="999", currency="USD")
    owned.transport = object()
    owned.configuration = object()
    unowned = Stock("ABC", old_key, name="N/A", exchange="N/A", current_price="N/A")
    zero = Stock("ZERO", old_key, amount_owned="0", cost_basis="0", current_price="0")
    original = Watch_list("Offline", [owned, owned, unowned, zero])
    candidate = watchlist_to_record(original, "menu_watchlist")
    repo = SQLiteWatchlistRepository(tmp_path / "state.sqlite3")
    repo.save(candidate)
    data = repo._path.read_bytes()
    assert old_key.encode() not in data and current_key.encode() not in data
    restored = record_to_watchlist(repo.get("menu_watchlist"), current_key)
    assert len(restored.stocks) == 4 and restored.name == "Offline"
    first, duplicate, absent, zero = restored.stocks
    assert first is not duplicate
    assert first.API_KEY == duplicate.API_KEY == absent.API_KEY == zero.API_KEY == current_key
    assert first.total_return == "20.0"
    assert first._snapshot.cost_basis == Decimal("25.00000000")
    assert first._snapshot.market_value == Decimal("30.00000000")
    assert first.amount_owned == "0.2500" and first.cost_basis == "100.0000"
    assert absent._position is None and absent.cost_basis == "-" and absent.current_price is None
    assert absent.name is absent.exchange is None
    assert zero._position is not None and zero.current_price == "0" and zero.total_return == "-"
    assert not hasattr(first, "transport") and not hasattr(first, "configuration")
    assert_entries(watchlist_to_record(restored, "menu_watchlist"), candidate)
    assert all(s.API_KEY is None for s in record_to_watchlist(candidate, None).stocks)


@pytest.mark.parametrize("field,value", [("name", " "), ("exchange", " NASDAQ"),
                                         ("sector", object()), ("price_5y", 1)])
def test_facade_invalid_fields_are_safe_validation_errors(field, value):
    from stock import Stock
    from watch_list import Watch_list
    from stock_tracker.compatibility.watchlist_persistence import watchlist_to_record
    from stock_tracker.exceptions import PersistenceValidationError
    facade = Stock("ABC", None)
    setattr(facade, field, value)
    with pytest.raises(PersistenceValidationError) as caught:
        watchlist_to_record(Watch_list("Example", [facade]), "menu")
    assert str(caught.value) == "Local storage input is invalid."
    assert caught.value.__suppress_context__



@pytest.mark.parametrize("field", ["namespace", "name", "entries"])
def test_deleted_record_fields_reject_safely_before_io(tmp_path, field):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceValidationError
    candidate = record("menu")
    object.__delattr__(candidate, field)
    path = tmp_path / "absent.sqlite3"
    with pytest.raises(PersistenceValidationError):
        SQLiteWatchlistRepository(path).save(candidate)
    assert not path.exists()


@pytest.mark.parametrize("field", ["stock", "quantity", "average_cost", "current_price", "country"])
def test_deleted_entry_fields_reject_safely_before_io(tmp_path, entry, field):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceValidationError
    object.__delattr__(entry, field)
    path = tmp_path / "absent.sqlite3"
    with pytest.raises(PersistenceValidationError):
        SQLiteWatchlistRepository(path).save(record("menu", [entry]))
    assert not path.exists()


@pytest.mark.parametrize("location", ["namespace", "name", "symbol", "stock_name", "exchange", "sector", "price_5y"])
def test_unrepresentable_text_refused_before_io_preserves_existing_state(tmp_path, entry, location):
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceValidationError
    path = tmp_path / "existing.sqlite3"
    repo = SQLiteWatchlistRepository(path)
    repo.save(record("valid", [entry]))
    before = path.read_bytes()
    invalid = chr(0xd800)
    candidate = record("menu", [entry])
    if location in ("namespace", "name"):
        object.__setattr__(candidate, location, invalid)
    elif location in ("symbol", "stock_name", "exchange"):
        object.__setattr__(entry.stock, "name" if location == "stock_name" else location, invalid)
    else:
        object.__setattr__(entry, location, invalid)
    absent = tmp_path / "absent.sqlite3"
    for target in (path, absent):
        with pytest.raises(PersistenceValidationError) as caught:
            SQLiteWatchlistRepository(target).save(candidate)
        assert str(caught.value) == "Local storage input is invalid."
        assert caught.value.__suppress_context__
    with pytest.raises(PersistenceValidationError):
        repo.get(invalid)
    assert not absent.exists() and path.read_bytes() == before


@pytest.mark.parametrize("operation", ["get", "list"])
def test_read_snapshot_does_not_mix_names_and_replaced_entries(tmp_path, monkeypatch, entry, operation):
    import threading
    from stock_tracker.persistence import sqlite_watchlists as module
    repo = module.SQLiteWatchlistRepository(tmp_path / "state.sqlite3")
    repo.save(record("menu", [entry], "Old"))
    changed = threading.Event()
    worker_errors = []
    actual_write, actual_read = module._write_watchlist, module._read_watchlist
    def signal_write(connection, candidate):
        actual_write(connection, candidate)
        changed.set()
    def writer():
        try:
            repo.save(record("menu", [], "New"))
        except BaseException as error:
            worker_errors.append(error)
            changed.set()
    workers = []
    def coordinated_read(connection, namespace, name):
        worker = threading.Thread(target=writer)
        workers.append(worker)
        worker.start()
        assert changed.wait(3), "writer did not reach uncommitted replacement"
        return actual_read(connection, namespace, name)
    monkeypatch.setattr(module, "_write_watchlist", signal_write)
    with monkeypatch.context() as guards:
        guards.setattr(module, "_read_watchlist", coordinated_read)
        found = repo.get("menu") if operation == "get" else repo.list()[0]
    for worker in workers:
        worker.join(5)
        assert not worker.is_alive()
    assert worker_errors == []
    assert found.name == "Old" and len(found.entries) == 1
    assert repo.get("menu").name == "New" and repo.get("menu").entries == ()



@pytest.mark.parametrize("location,field", [("record", "name"), ("entry", "quantity"),
                                           ("stock", "exchange"), ("entry", "sector")])
def test_mapping_deleted_record_fields_reject_safely(entry, location, field):
    from stock_tracker.compatibility.watchlist_persistence import record_to_watchlist
    from stock_tracker.exceptions import PersistenceValidationError
    candidate = record("menu", [entry])
    target = {"record": candidate, "entry": entry, "stock": entry.stock}[location]
    object.__delattr__(target, field)
    with pytest.raises(PersistenceValidationError):
        record_to_watchlist(candidate, None)


@pytest.mark.parametrize("field", ["name", "exchange", "sector", "_position", "_price_text"])
def test_mapping_deleted_facade_fields_reject_safely(field):
    from stock import Stock
    from watch_list import Watch_list
    from stock_tracker.compatibility.watchlist_persistence import watchlist_to_record
    from stock_tracker.exceptions import PersistenceValidationError
    facade = Stock("ABC", None)
    delattr(facade, field)
    with pytest.raises(PersistenceValidationError):
        watchlist_to_record(Watch_list("Example", [facade]), "menu")


@pytest.mark.parametrize("failure", ["commit", "unexpected"])
def test_failure_rolls_back_and_closes_acquired_connection(tmp_path, monkeypatch, entry, failure):
    from stock_tracker.persistence import connection as boundary
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.exceptions import PersistenceError
    path = tmp_path / "state.sqlite3"
    repo = SQLiteWatchlistRepository(path)
    repo.save(record("menu", [entry], "Old"))
    actual_connect = sqlite3.connect
    closed = []
    class FailingConnection(sqlite3.Connection):
        def commit(self):
            if failure == "commit":
                raise sqlite3.OperationalError("private commit failure")
            return super().commit()
        def execute(self, sql, parameters=()):
            if failure == "unexpected" and sql.startswith("DELETE FROM watchlist_entries"):
                raise RuntimeError("programming failure")
            return super().execute(sql, parameters)
        def close(self):
            closed.append(True)
            return super().close()
    with monkeypatch.context() as guards:
        guards.setattr(boundary.sqlite3, "connect", lambda *args, **kwargs:
                       actual_connect(*args, **kwargs, factory=FailingConnection))
        with pytest.raises(PersistenceError if failure == "commit" else RuntimeError):
            repo.save(record("menu", [], "New"))
    assert closed == [True]
    assert repo.get("menu").name == "Old" and len(repo.get("menu").entries) == 1
