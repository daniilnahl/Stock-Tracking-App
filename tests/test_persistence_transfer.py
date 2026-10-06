"""Strict neutral import and safe copies against real temporary SQLite files."""

import copy
import json
import os
from pathlib import Path
import sqlite3

import pytest


def payload():
    stock = {"symbol": "ABC", "name": "Example", "exchange": "NASDAQ"}
    position = {"stock": stock, "quantity": "0.2500", "average_cost": "100.123456789012345678901234567890"}
    entry = dict(position, current_price="0.00", sector="Tech", country=None, currency="USD",
                 market_cap="1.000B", price_1d="", price_5d="N/A", price_30d="-", price_3m=None,
                 price_6m="0", price_1y="1", price_3y="2", price_5y="3")
    return {"format": "stock-tracker-neutral", "version": 1,
            "portfolios": [{"id": None, "name": "Allocated", "positions": [position, position]},
                           {"id": "5", "name": "Explicit", "positions": []}],
            "watchlists": [{"namespace": "menu_watchlist", "name": "Example", "entries": [entry, entry]},
                           {"namespace": "daniils_stock_method", "name": "Other", "entries": []}]}


def source_file(tmp_path, data=None):
    source = tmp_path / "neutral.json"
    source.write_text(json.dumps(payload() if data is None else data), encoding="utf-8")
    return source


def test_import_exact_records_reserves_explicit_ids_and_preserves_source(tmp_path):
    from stock_tracker.persistence.transfer import import_neutral_state
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    source = source_file(tmp_path)
    original = source.read_bytes()
    legacy = tmp_path / "watchlist.pkl"
    legacy.write_bytes(b"fictional opaque legacy bytes; never opened by utility")
    destination = tmp_path / "state.sqlite3"
    import_neutral_state(source, destination)
    portfolios = SQLitePortfolioRepository(destination).list()
    assert [p.id for p in portfolios] == [5, 6]
    assert portfolios[1].positions[0].quantity.as_tuple().exponent == -4
    assert str(portfolios[1].positions[0].average_cost) == "100.123456789012345678901234567890"
    watchlists = SQLiteWatchlistRepository(destination).list()
    assert [w.namespace for w in watchlists] == ["daniils_stock_method", "menu_watchlist"]
    assert len(watchlists[1].entries) == 2
    assert str(watchlists[1].entries[0].current_price) == "0.00"
    assert source.read_bytes() == original and legacy.read_bytes().startswith(b"fictional opaque")


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(extra="unknown"), lambda p: p.pop("format"),
    lambda p: p.update(version=True), lambda p: p.update(version=1.0),
    lambda p: p.update(format="other"), lambda p: p.update(portfolios={}),
    lambda p: p["portfolios"][0].update(id=True),
    lambda p: p["portfolios"][0].update(id="01"),
    lambda p: p["portfolios"][0].update(id="-0"),
    lambda p: p["portfolios"][0].update(id="+1"),
    lambda p: p["portfolios"][0].update(id="1 "),
    lambda p: p["portfolios"][0].update(name=" bad "),
    lambda p: p["portfolios"][0]["positions"][0].update(quantity=1),
    lambda p: p["portfolios"][0]["positions"][0].update(quantity=True),
    lambda p: p["portfolios"][0]["positions"][0].update(quantity="NaN"),
    lambda p: p["portfolios"][0]["positions"][0].update(quantity=" 1"),
    lambda p: p["portfolios"][0]["positions"][0].update(quantity="1_0"),
    lambda p: p["portfolios"][0]["positions"][0].update(quantity="-1"),
    lambda p: p["portfolios"][0]["positions"][0].update(average_cost=None),
    lambda p: p["portfolios"][0]["positions"][0]["stock"].update(symbol=""),
    lambda p: p["portfolios"][0]["positions"][0]["stock"].update(extra="unknown"),
    lambda p: p["watchlists"][0]["entries"][0].update(average_cost=None),
    lambda p: p["watchlists"][0]["entries"][0].update(current_price="Infinity"),
    lambda p: p["watchlists"][0]["entries"][0].update(sector=1),
    lambda p: p["watchlists"][0]["entries"][0].pop("country"),
    lambda p: p["watchlists"].append(copy.deepcopy(p["watchlists"][0])),
    lambda p: p["portfolios"].append(copy.deepcopy(p["portfolios"][1])),
    lambda p: p["watchlists"][0].update(name=chr(0xd800)),
])
def test_invalid_full_payload_never_opens_destination(tmp_path, mutation, monkeypatch):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceValidationError
    data = payload()
    mutation(data)
    source = source_file(tmp_path, data)
    before = source.read_bytes()
    monkeypatch.setattr(transfer, "database_connection", lambda *args, **kwargs: pytest.fail("invalid payload opened destination"))
    with pytest.raises(PersistenceValidationError) as caught:
        transfer.import_neutral_state(source, tmp_path / "absent.sqlite3")
    assert str(caught.value) == "Local storage input is invalid."
    assert source.read_bytes() == before


@pytest.mark.parametrize("text", ['{"format":"a","format":"b"}', '{"a":NaN}', '{"a":Infinity}',
                                 '{"a":-Infinity}', 'not JSON', '{"a":1e100000}',
                                 '[' * 65 + '0' + ']' * 65])
def test_adversarial_json_refused_without_writes(tmp_path, text):
    from stock_tracker.persistence.transfer import import_neutral_state
    from stock_tracker.exceptions import PersistenceValidationError
    source = tmp_path / "bad.json"
    source.write_text(text, encoding="utf-8")
    destination = tmp_path / "absent.sqlite3"
    with pytest.raises(PersistenceValidationError):
        import_neutral_state(source, destination)
    assert not destination.exists()


@pytest.mark.parametrize("limit", ["MAX_BYTES", "MAX_AGGREGATES", "MAX_ENTRIES", "MAX_STRING", "MAX_DEPTH"])
def test_each_resource_limit_refuses_before_destination_io(tmp_path, monkeypatch, limit):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceValidationError
    source = source_file(tmp_path)
    monkeypatch.setattr(transfer, limit, 1)
    with pytest.raises(PersistenceValidationError):
        transfer.import_neutral_state(source, tmp_path / "absent.sqlite3")
    assert not (tmp_path / "absent.sqlite3").exists()


def test_string_cap_exact_boundary_and_quoted_braces(tmp_path):
    from stock_tracker.persistence.transfer import import_neutral_state
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    from stock_tracker.exceptions import PersistenceValidationError
    data = payload()
    data["portfolios"][0]["name"] = "{" * 4096
    source = source_file(tmp_path, data)
    destination = tmp_path / "state.sqlite3"
    import_neutral_state(source, destination)
    assert len(SQLitePortfolioRepository(destination).get(6).name) == 4096
    data["portfolios"][0]["name"] += "{"
    source_file(tmp_path, data)
    with pytest.raises(PersistenceValidationError):
        import_neutral_state(source, tmp_path / "absent.sqlite3")
    assert not (tmp_path / "absent.sqlite3").exists()


def test_optional_unowned_signedzero_quote_and_empty_metadata(tmp_path):
    from stock_tracker.persistence.transfer import import_neutral_state
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    data = payload()
    entry = data["watchlists"][0]["entries"][0]
    entry.update(quantity="-0.000", average_cost=None, current_price=None)
    import_neutral_state(source_file(tmp_path, data), tmp_path / "state.sqlite3")
    found = SQLiteWatchlistRepository(tmp_path / "state.sqlite3").get("menu_watchlist").entries[0]
    assert str(found.quantity) == "-0.000" and found.average_cost is found.current_price is None
    assert found.price_1d == "" and found.price_5d == "N/A"


def test_collisions_refuse_without_replacing_or_partial_additions(tmp_path):
    from stock_tracker.persistence.transfer import import_neutral_state
    from stock_tracker.exceptions import PersistenceConflictError
    source, destination = source_file(tmp_path), tmp_path / "state.sqlite3"
    import_neutral_state(source, destination)
    before = destination.read_bytes()
    data = payload()
    data["portfolios"].insert(0, {"id": "99", "name": "Would be new", "positions": []})
    source_file(tmp_path, data)
    with pytest.raises(PersistenceConflictError):
        import_neutral_state(source, destination)
    assert destination.read_bytes() == before


@pytest.mark.parametrize("existing", [False, True])
def test_partial_import_failure_rolls_back_schema_and_records(tmp_path, monkeypatch, existing):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceError
    from stock_tracker.persistence.migrations import migrate_database
    destination = tmp_path / "state.sqlite3"
    if existing:
        migrate_database(destination)
        before = destination.read_bytes()
    actual_write = transfer._write_watchlist
    def fail(connection, record):
        actual_write(connection, record)
        raise sqlite3.OperationalError("private failed write")
    monkeypatch.setattr(transfer, "_write_watchlist", fail)
    with pytest.raises(PersistenceError) as caught:
        transfer.import_neutral_state(source_file(tmp_path), destination)
    assert str(caught.value) == "Local storage operation failed."
    if existing:
        assert destination.read_bytes() == before
    else:
        with sqlite3.connect(destination) as connection:
            assert connection.execute("PRAGMA user_version").fetchone() == (0,)
            assert connection.execute("SELECT name FROM sqlite_schema WHERE type='table'").fetchall() == []


@pytest.mark.parametrize("operation", ["import_neutral_state", "backup_database", "restore_database"])
@pytest.mark.parametrize("alias", ["same", "hardlink"])
def test_aliases_refused_before_modification(tmp_path, operation, alias):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceValidationError
    source = source_file(tmp_path)
    destination = source
    if alias == "hardlink":
        destination = tmp_path / "alias"
        os.link(source, destination)
    before = source.read_bytes()
    with pytest.raises(PersistenceValidationError):
        getattr(transfer, operation)(source, destination)
    assert source.read_bytes() == before and destination.read_bytes() == before


def test_backup_and_restore_reopen_all_data(tmp_path):
    from stock_tracker.persistence.transfer import import_neutral_state, backup_database, restore_database
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    original, backup, restored = (tmp_path / name for name in ("original.sqlite3", "backup.sqlite3", "restored.sqlite3"))
    import_neutral_state(source_file(tmp_path), original)
    before = original.read_bytes()
    backup_database(original, backup)
    restore_database(backup, restored)
    assert original.read_bytes() == before
    assert [p.id for p in SQLitePortfolioRepository(restored).list()] == [5, 6]
    assert len(SQLiteWatchlistRepository(restored).get("menu_watchlist").entries) == 2
    with sqlite3.connect(restored) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_backup_includes_active_wal_committed_state(tmp_path):
    from stock_tracker.persistence.transfer import import_neutral_state, backup_database
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    source, destination = tmp_path / "original.sqlite3", tmp_path / "backup.sqlite3"
    import_neutral_state(source_file(tmp_path), source)
    connection = sqlite3.connect(source)
    try:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        connection.execute("UPDATE watchlists SET name=? WHERE namespace=?", ("Committed WAL", "menu_watchlist"))
        connection.commit()
        assert Path(str(source) + "-wal").exists()
        connection.execute("UPDATE watchlists SET name=? WHERE namespace=?", ("Uncommitted", "menu_watchlist"))
        backup_database(source, destination)
        assert SQLiteWatchlistRepository(destination).get("menu_watchlist").name == "Committed WAL"
    finally:
        connection.rollback()
        connection.close()


@pytest.mark.parametrize("corruption", ["version", "quantity", "ordinal", "ownership", "orphan", "bytes"])
def test_backup_refuses_invalid_source_before_reserving_destination(tmp_path, corruption):
    from stock_tracker.persistence.transfer import import_neutral_state, backup_database
    from stock_tracker.exceptions import PersistenceError
    source, destination = tmp_path / "original.sqlite3", tmp_path / "backup.sqlite3"
    import_neutral_state(source_file(tmp_path), source)
    if corruption == "bytes":
        source.write_bytes(b"corrupt database")
    else:
        with sqlite3.connect(source) as connection:
            sql = {"version": "PRAGMA user_version=99",
                   "quantity": "UPDATE positions SET quantity='NaN'",
                   "ordinal": "UPDATE positions SET ordinal=ordinal+5",
                   "ownership": "UPDATE watchlist_entries SET average_cost=NULL",
                   "orphan": "DELETE FROM watchlists"}[corruption]
            connection.execute(sql)
    before = source.read_bytes()
    with pytest.raises(PersistenceError):
        backup_database(source, destination)
    assert source.read_bytes() == before and not destination.exists()


@pytest.mark.parametrize("operation", ["backup_database", "restore_database"])
def test_copy_never_overwrites_existing_destination(tmp_path, operation):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceConflictError
    source = source_file(tmp_path)
    destination = tmp_path / "existing.sqlite3"
    destination.write_bytes(b"existing contents")
    with pytest.raises(PersistenceConflictError):
        getattr(transfer, operation)(source, destination)
    assert destination.read_bytes() == b"existing contents"


def test_dangling_destination_entry_refused_without_creating_target(tmp_path, monkeypatch):
    from stock_tracker.persistence.transfer import import_neutral_state, backup_database
    from stock_tracker.exceptions import PersistenceConflictError
    source, destination, target = tmp_path / "source.sqlite3", tmp_path / "dangling.sqlite3", tmp_path / "target.sqlite3"
    import_neutral_state(source_file(tmp_path), source)
    try:
        destination.symlink_to(target)
    except OSError:
        # Windows hosts may prohibit creating symlinks; model that directory entry
        # through the filesystem boundary without altering permissions/skipping.
        actual_lstat = Path.lstat
        actual_resolve = Path.resolve
        def lstat(path):
            return source.stat() if path == destination else actual_lstat(path)
        def resolve(path, *args, **kwargs):
            return target if path == destination else actual_resolve(path, *args, **kwargs)
        monkeypatch.setattr(Path, "lstat", lstat)
        monkeypatch.setattr(Path, "resolve", resolve)
    before = source.read_bytes()
    with pytest.raises(PersistenceConflictError):
        backup_database(source, destination)
    assert source.read_bytes() == before and not target.exists()


def test_existing_invalid_records_refuse_import_without_changes(tmp_path):
    from stock_tracker.persistence.transfer import import_neutral_state
    from stock_tracker.exceptions import PersistenceDataError
    source = source_file(tmp_path)
    destination = tmp_path / "state.sqlite3"
    import_neutral_state(source, destination)
    with sqlite3.connect(destination) as connection:
        connection.execute("UPDATE positions SET quantity='NaN'")
    data = payload()
    data.update(portfolios=[], watchlists=[{"namespace": "new", "name": "New", "entries": []}])
    source_file(tmp_path, data)
    before = destination.read_bytes()
    with pytest.raises(PersistenceDataError):
        import_neutral_state(source, destination)
    assert destination.read_bytes() == before


@pytest.mark.parametrize("limit", ["bytes", "aggregates", "entries"])
def test_actual_approved_limits_refuse_before_writes(tmp_path, limit):
    from stock_tracker.persistence.transfer import import_neutral_state, MAX_BYTES, MAX_AGGREGATES, MAX_ENTRIES
    from stock_tracker.exceptions import PersistenceValidationError
    source = tmp_path / "limit.json"
    if limit == "bytes":
        source.write_bytes(b" " * (MAX_BYTES + 1))
    else:
        data = {"format": "stock-tracker-neutral", "version": 1, "portfolios": [], "watchlists": []}
        if limit == "aggregates":
            data["portfolios"] = [{"id": None, "name": "A", "positions": []}] * (MAX_AGGREGATES + 1)
        else:
            position = {"stock": {"symbol": "A", "name": None, "exchange": None},
                        "quantity": "0", "average_cost": "0"}
            data["portfolios"] = [{"id": None, "name": "A", "positions": [position] * (MAX_ENTRIES + 1)}]
        source.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        assert source.stat().st_size <= MAX_BYTES
    destination = tmp_path / "absent.sqlite3"
    with pytest.raises(PersistenceValidationError):
        import_neutral_state(source, destination)
    assert not destination.exists()


def test_bounded_source_read_and_invalid_utf8_never_create_destination(tmp_path, monkeypatch):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceValidationError
    source = tmp_path / "invalid.json"
    source.write_bytes(b"\xff")
    sizes = []
    actual_open = Path.open
    class Reader:
        def __init__(self, original):
            self.original = original
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.original.close()
        def read(self, size):
            sizes.append(size)
            return self.original.read(size)
    def bounded_open(path, *args, **kwargs):
        opened = actual_open(path, *args, **kwargs)
        return Reader(opened) if path == source and args == ("rb",) else opened
    monkeypatch.setattr(Path, "open", bounded_open)
    with pytest.raises(PersistenceValidationError):
        transfer.import_neutral_state(source, tmp_path / "absent.sqlite3")
    assert sizes == [transfer.MAX_BYTES + 1]
    assert not (tmp_path / "absent.sqlite3").exists()


def test_canonical_large_id_transfer_exact_at_string_cap(tmp_path):
    from stock_tracker.persistence.transfer import import_neutral_state
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    from decimal import Decimal
    data = {"format": "stock-tracker-neutral", "version": 1, "portfolios": [
        {"id": "9" * 4096, "name": "Exact ID", "positions": []},
        {"id": None, "name": "Allocated ID", "positions": []}], "watchlists": []}
    source = source_file(tmp_path, data)
    destination = tmp_path / "state.sqlite3"
    import_neutral_state(source, destination)
    records = SQLitePortfolioRepository(destination).list()
    explicit = int(Decimal("9" * 4096))
    assert [p.id for p in records] == [explicit, explicit + 1]


def test_additions_preserve_distinct_existing_records_and_allocate_above_existing(tmp_path):
    from stock_tracker.persistence.transfer import import_neutral_state
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.domain import Portfolio
    destination = tmp_path / "state.sqlite3"
    SQLitePortfolioRepository(destination).create(Portfolio(20, "Existing"))
    import_neutral_state(source_file(tmp_path), destination)
    assert [p.id for p in SQLitePortfolioRepository(destination).list()] == [5, 20, 21]
    assert len(SQLiteWatchlistRepository(destination).list()) == 2


def test_copy_exclusive_reservation_refuses_competing_creation(tmp_path, monkeypatch):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceConflictError
    source, destination = tmp_path / "source.sqlite3", tmp_path / "backup.sqlite3"
    transfer.import_neutral_state(source_file(tmp_path), source)
    original_reserve = transfer._reserve
    def race(path):
        path.write_bytes(b"competing file")
        return original_reserve(path)
    monkeypatch.setattr(transfer, "_reserve", race)
    with pytest.raises(PersistenceConflictError):
        transfer.backup_database(source, destination)
    assert destination.read_bytes() == b"competing file"


@pytest.mark.parametrize("failure", ["backup", "postcopy", "unexpected"])
def test_copy_failure_closes_connections_preserves_source_and_leaves_reserved_file(tmp_path, monkeypatch, failure):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceError
    source, destination = tmp_path / "source.sqlite3", tmp_path / "backup.sqlite3"
    transfer.import_neutral_state(source_file(tmp_path), source)
    before = source.read_bytes()
    actual_connect = sqlite3.connect
    closed = []
    class Tracked(sqlite3.Connection):
        def backup(self, other, *args, **kwargs):
            if failure == "backup":
                raise sqlite3.OperationalError("private backup failure")
            if failure == "unexpected":
                raise RuntimeError("programming failure")
            return super().backup(other, *args, **kwargs)
        def close(self):
            closed.append(True)
            return super().close()
    monkeypatch.setattr(transfer.sqlite3, "connect", lambda *args, **kwargs:
                        actual_connect(*args, **kwargs, factory=Tracked))
    if failure == "postcopy":
        original_validate = transfer._validate_database
        count = 0
        def fail_second(connection):
            nonlocal count
            count += 1
            original_validate(connection)
            if count == 2:
                raise sqlite3.OperationalError("private verification failure")
        monkeypatch.setattr(transfer, "_validate_database", fail_second)
    with pytest.raises(RuntimeError if failure == "unexpected" else PersistenceError) as caught:
        transfer.backup_database(source, destination)
    if failure != "unexpected":
        assert str(caught.value) == "Local storage operation failed."
        assert caught.value.__suppress_context__
    assert closed == [True, True]
    assert source.read_bytes() == before and destination.exists()


@pytest.mark.parametrize("corruption", ["watchlist_decimal", "watchlist_ordinal", "watchlist_metadata", "portfolio_name", "stock_identity"])
def test_checked_copy_validates_every_application_record(tmp_path, corruption):
    from stock_tracker.persistence.transfer import import_neutral_state, restore_database
    from stock_tracker.exceptions import PersistenceDataError
    source, destination = tmp_path / "source.sqlite3", tmp_path / "restored.sqlite3"
    import_neutral_state(source_file(tmp_path), source)
    with sqlite3.connect(source) as connection:
        sql = {"watchlist_decimal": "UPDATE watchlist_entries SET current_price='NaN'",
               "watchlist_ordinal": "UPDATE watchlist_entries SET ordinal=ordinal+5",
               "watchlist_metadata": "UPDATE watchlist_entries SET sector=X'FF'",
               "portfolio_name": "UPDATE portfolios SET name=''",
               "stock_identity": "UPDATE positions SET exchange=' '"}[corruption]
        connection.execute(sql)
    with pytest.raises(PersistenceDataError):
        restore_database(source, destination)
    assert not destination.exists()


def test_destination_permission_failure_is_sanitized_before_copy(tmp_path, monkeypatch):
    from stock_tracker.persistence.transfer import import_neutral_state, backup_database
    from stock_tracker.exceptions import PersistenceError
    source, destination = tmp_path / "source.sqlite3", tmp_path / "backup.sqlite3"
    import_neutral_state(source_file(tmp_path), source)
    actual_lstat = Path.lstat
    def denied(path):
        if path == destination:
            raise PermissionError("private destination")
        return actual_lstat(path)
    monkeypatch.setattr(Path, "lstat", denied)
    with pytest.raises(PersistenceError) as caught:
        backup_database(source, destination)
    assert str(caught.value) == "Local storage operation failed."
    assert caught.value.__suppress_context__
    assert not destination.exists()


def test_backup_keeps_one_validated_snapshot_during_concurrent_committed_change(tmp_path, monkeypatch):
    from stock_tracker.persistence import transfer
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    source, destination = tmp_path / "source.sqlite3", tmp_path / "backup.sqlite3"
    transfer.import_neutral_state(source_file(tmp_path), source)
    keeper = sqlite3.connect(source)
    try:
        keeper.execute("PRAGMA journal_mode=WAL")
        actual_validate = transfer._validate_database
        validations = 0
        def concurrent_change(connection):
            nonlocal validations
            actual_validate(connection)
            validations += 1
            if validations == 1:
                with sqlite3.connect(source) as writer:
                    writer.execute("UPDATE watchlists SET name=? WHERE namespace=?", ("After snapshot", "menu_watchlist"))
        monkeypatch.setattr(transfer, "_validate_database", concurrent_change)
        transfer.backup_database(source, destination)
        assert SQLiteWatchlistRepository(destination).get("menu_watchlist").name == "Example"
        assert SQLiteWatchlistRepository(source).get("menu_watchlist").name == "After snapshot"
    finally:
        keeper.close()


def test_excessive_depth_refused_before_json_decoder(tmp_path, monkeypatch):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceValidationError
    source = tmp_path / "deep.json"
    source.write_text("[" * 65 + "0" + "]" * 65, encoding="utf-8")
    monkeypatch.setattr(transfer.json, "loads", lambda *args, **kwargs: pytest.fail("depth bound was not checked before JSON decode"))
    with pytest.raises(PersistenceValidationError):
        transfer.import_neutral_state(source, tmp_path / "absent.sqlite3")


def test_changed_reservation_identity_refused_before_sqlite_copy_open(tmp_path, monkeypatch):
    from stock_tracker.persistence import transfer
    from stock_tracker.exceptions import PersistenceConflictError
    source, destination = tmp_path / "source.sqlite3", tmp_path / "backup.sqlite3"
    transfer.import_neutral_state(source_file(tmp_path), source)
    before = source.read_bytes()
    original_copy = transfer._copy_connection
    original_stat = Path.stat
    def changed_identity(path, reserved):
        def replacement_stat(candidate, *args, **kwargs):
            return original_stat(source) if candidate == destination else original_stat(candidate, *args, **kwargs)
        monkeypatch.setattr(Path, "stat", replacement_stat)
        return original_copy(path, reserved)
    monkeypatch.setattr(transfer, "_copy_connection", changed_identity)
    with pytest.raises(PersistenceConflictError):
        transfer.backup_database(source, destination)
    assert source.read_bytes() == before
    assert destination.read_bytes() == b""
