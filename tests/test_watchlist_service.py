"""Local application use cases with real calculations and isolated SQLite state."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
from pathlib import Path
import sqlite3

import pytest


def entry(symbol="AAPL", *, name="Fictional", exchange="NASDAQ", quantity="10", cost="100", price="120"):
    from stock_tracker.domain import Stock
    from stock_tracker.persistence.models import WatchlistEntry
    return WatchlistEntry(Stock(symbol, name, exchange), Decimal(quantity),
                          None if cost is None else Decimal(cost),
                          None if price is None else Decimal(price),
                          "Tech", "US", "USD", "opaque cap", "", "literal [x]", None,
                          "0", "-", "N/A", "2.50", "old")


def record(*entries, namespace="menu_watchlist"):
    from stock_tracker.persistence.models import WatchlistRecord
    return WatchlistRecord(namespace, "Saved", tuple(entries))


class Repository:
    def __init__(self, value=None):
        self.value, self.calls = value, []

    def get(self, namespace):
        self.calls.append(("get", namespace))
        return self.value

    def save(self, candidate):
        self.calls.append(("save", candidate))
        self.value = candidate


def service(repository, legacy=lambda: False, namespace="menu_watchlist"):
    from stock_tracker.services import WatchlistService
    return WatchlistService(repository, namespace=namespace, legacy_present=legacy)


def test_constructor_is_lazy_and_empty_load_has_explicit_namespace():
    repository = Repository()
    calls = []
    subject = service(repository, lambda: calls.append("legacy") or False)
    assert repository.calls == calls == []
    result = subject.load()
    assert (result.namespace, result.name, result.entries) == ("menu_watchlist", "Watchlist", ())
    assert repository.calls == [("get", "menu_watchlist")]
    assert calls == ["legacy"]


def test_existing_namespace_never_checks_legacy_and_preserves_unknown_stock_identity():
    original = record(entry(exchange=None), entry(exchange=None))
    def denied():
        pytest.fail("Existing namespace inspected legacy entry")
    subject = service(Repository(original), denied)
    restored = subject.load()
    assert restored == original
    assert restored.entries[0].stock is original.entries[0].stock
    assert restored.entries[1].stock is original.entries[1].stock
    assert restored.entries[0].stock != restored.entries[1].stock


@pytest.mark.parametrize("operation", ["load", "save"])
def test_absent_namespace_with_legacy_refuses_without_save(operation):
    from stock_tracker.exceptions import LegacyStatePresentError
    repository = Repository()
    subject = service(repository, lambda: True)
    with pytest.raises(LegacyStatePresentError):
        subject.load() if operation == "load" else subject.save(record(entry()))
    assert repository.calls == [("get", "menu_watchlist")]


def test_save_validates_complete_candidate_before_any_dependency_call():
    from stock_tracker.exceptions import PersistenceValidationError
    repository = Repository()
    subject = service(repository, lambda: pytest.fail("Invalid candidate checked legacy"))
    original = entry()
    object.__setattr__(original, "quantity", Decimal("NaN"))
    with pytest.raises(PersistenceValidationError):
        subject.save(record(original))
    assert repository.calls == []


@pytest.mark.parametrize("operation", ["load", "save", "view", "remove"])
def test_namespace_mismatch_is_safe_and_never_saved(operation):
    from stock_tracker.exceptions import PersistenceValidationError
    wrong = record(entry(), namespace="daniils_stock_method")
    repository = Repository(wrong)
    subject = service(repository)
    with pytest.raises(PersistenceValidationError):
        if operation == "load":
            subject.load()
        elif operation == "remove":
            subject.remove(wrong, "AAPL")
        else:
            getattr(subject, operation)(wrong)
    assert repository.calls == ([('get', 'menu_watchlist')] if operation == "load" else [])


@pytest.mark.parametrize("field,value", [
    ("name", ""), ("entries", []), ("entries", (object(),)), ("namespace", "private\ud800"),
])
def test_mutated_frozen_record_is_revalidated(field, value):
    from stock_tracker.exceptions import PersistenceValidationError
    original = record(entry())
    object.__setattr__(original, field, value)
    repository = Repository(original)
    with pytest.raises(PersistenceValidationError):
        service(repository).load()
    assert repository.calls == [("get", "menu_watchlist")]


@pytest.mark.parametrize("field,value", [("symbol", ""), ("name", "private\ud800"), ("exchange", " NASDAQ")])
def test_nested_mutated_stock_is_revalidated_before_save(field, value):
    from stock_tracker.exceptions import PersistenceValidationError
    original = entry()
    object.__setattr__(original.stock, field, value)
    repository = Repository()
    with pytest.raises(PersistenceValidationError):
        service(repository).save(record(original))
    assert repository.calls == []


def test_missing_optional_stock_field_is_malformed_and_does_not_save():
    from stock_tracker.exceptions import PersistenceValidationError
    original = entry()
    object.__delattr__(original.stock, "name")
    repository = Repository()
    with pytest.raises(PersistenceValidationError):
        service(repository).save(record(original))
    assert repository.calls == []


def test_save_refuses_malformed_injected_existing_record():
    from stock_tracker.exceptions import PersistenceValidationError
    original = record(entry())
    object.__setattr__(original.entries[0], "current_price", Decimal("NaN"))
    repository = Repository(original)
    with pytest.raises(PersistenceValidationError):
        service(repository).save(record(entry("OTHER")))
    assert repository.calls == [("get", "menu_watchlist")]


@pytest.mark.parametrize("namespace", [None, "", " menu_watchlist", "private\ud800"])
def test_invalid_namespace_is_rejected_without_io(namespace):
    from stock_tracker.exceptions import PersistenceValidationError
    repository = Repository()
    with pytest.raises(PersistenceValidationError):
        service(repository, namespace=namespace)
    assert repository.calls == []


def test_non_boolean_legacy_result_is_rejected():
    from stock_tracker.exceptions import PersistenceValidationError
    with pytest.raises(PersistenceValidationError):
        service(Repository(), lambda: 1).load()


@pytest.mark.parametrize("kind", ["repository", "legacy", "programming"])
def test_dependency_failures_propagate_without_replacement(kind):
    from stock_tracker.exceptions import PersistenceError
    failure = RuntimeError("programming") if kind == "programming" else PersistenceError()
    repository = Repository()
    def fail(*args):
        raise failure
    if kind == "legacy":
        subject = service(repository, fail)
    else:
        repository.get = fail
        subject = service(repository)
    with pytest.raises(type(failure)) as caught:
        subject.load()
    assert caught.value is failure
    assert repository.value is None


def test_known_value_view_is_numeric_and_does_not_mutate_or_perform_io():
    original = record(entry())
    repository = Repository()
    subject = service(repository, lambda: pytest.fail("View inspected legacy"))
    result = subject.view(original)
    snapshot = result.entries[0].snapshot
    assert (snapshot.cost_basis, snapshot.market_value, snapshot.unrealized_pnl,
            snapshot.unrealized_return) == (Decimal(1000), Decimal(1200), Decimal(200), Decimal("0.20"))
    assert result.record == original
    assert result.entries[0].entry.price_1d == "" and result.entries[0].entry.price_5d == "literal [x]"
    assert original.entries[0].average_cost == Decimal(100)
    assert repository.calls == []
    with pytest.raises(FrozenInstanceError):
        result.entries = ()


@pytest.mark.parametrize("quantity,cost,price,expected", [
    ("0", None, None, None),
    ("0", "0", "120", ("0", "0", "0", None)),
    ("0", "100", None, ("0", None, None, None)),
    ("10", "0", "120", ("0", "1200", "1200", None)),
    ("0.25", "100", "80", ("25", "20", "-5", "-0.2")),
])
def test_view_preserves_unowned_zero_missing_and_fractional_distinctions(quantity, cost, price, expected):
    row = entry(quantity=quantity, cost=cost, price=price)
    result = service(Repository()).view(record(row)).entries[0].snapshot
    if expected is None:
        assert result is None
    else:
        assert (result.cost_basis, result.market_value, result.unrealized_pnl, result.unrealized_return) == tuple(
            None if value is None else Decimal(value) for value in expected
        )


def test_view_retains_caller_decimal_context_and_ordered_duplicate_rows():
    rows = (entry(quantity="0.12345678901234567890123456789"), entry(exchange="NYSE"), entry(exchange=None))
    with localcontext() as context:
        context.prec = 50
        result = service(Repository()).view(record(*rows))
        assert result.entries[0].snapshot.cost_basis == Decimal("12.34567890123456789012345678900")
        assert context.prec == 50
    assert [row.entry.stock.exchange for row in result.entries] == ["NASDAQ", "NYSE", None]
    assert result.entries[0].entry.quantity.as_tuple() == rows[0].quantity.as_tuple()


@pytest.mark.parametrize("symbols,expected_names", [
    ([], []), (["B"], ["0"]), (["A", "A"], ["1"]),
    (["A", "A", "A"], ["1"]), (["A", "B", "A", "B"], ["1", "3"]),
    (["B", "A", "A", "B"], ["0", "2", "3"]),
])
def test_remove_preserves_accepted_forward_iteration_behavior_and_does_not_save(symbols, expected_names):
    original = record(*(entry(symbol, name=str(index)) for index, symbol in enumerate(symbols)))
    repository = Repository()
    result = service(repository).remove(original, "A")
    assert [row.stock.name for row in result.entries] == expected_names
    assert len(original.entries) == len(symbols)
    assert repository.calls == []


def test_remove_exact_symbol_does_not_normalize_identity():
    original = record(entry("aapl"), entry("AAPL", exchange="NYSE"))
    result = service(Repository()).remove(original, "AAPL")
    assert [row.stock.symbol for row in result.entries] == ["aapl"]


def test_remove_preserves_distinct_equal_valued_rows_by_ordinal():
    rows = tuple(entry("A") for _ in range(3))
    result = service(Repository()).remove(record(*rows), "A")
    assert len(result.entries) == 1
    assert result.entries[0].stock is rows[1].stock


def test_real_sqlite_precise_restart_independent_namespaces_and_missing_no_create(tmp_path):
    from stock_tracker.cli.storage import LegacyFilePresence
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    database = tmp_path / "state.sqlite3"
    legacy = tmp_path / "opaque.pkl"
    repository = SQLiteWatchlistRepository(database)
    first = service(repository, LegacyFilePresence(legacy))
    assert first.load().entries == ()
    assert not database.exists()
    precise = entry(quantity="0.12345678901234567890123456789", cost="100.0000000001", price=None)
    original = record(precise, entry(exchange="NYSE", quantity="0", cost=None, price="0"))
    first.save(original)
    legacy.write_bytes(b"opaque synthetic legacy; do not read")
    second = service(repository, lambda: False, "daniils_stock_method")
    second.save(record(entry("OTHER"), namespace="daniils_stock_method"))
    before = database.read_bytes()
    fresh = service(SQLiteWatchlistRepository(database), LegacyFilePresence(legacy))
    restored = fresh.load()
    assert restored == original
    assert str(restored.entries[0].quantity) == "0.12345678901234567890123456789"
    assert str(restored.entries[0].average_cost) == "100.0000000001"
    assert restored.entries[1].average_cost is None and restored.entries[1].current_price == 0
    assert fresh.view(restored).entries[0].snapshot.market_value is None
    assert database.read_bytes() == before
    assert second.load().entries[0].stock.symbol == "OTHER"
    assert legacy.read_bytes() == b"opaque synthetic legacy; do not read"


@pytest.mark.parametrize("kind", ["corrupt", "future", "malformed"])
def test_real_bad_sqlite_never_becomes_empty_or_replaced(tmp_path, kind):
    from stock_tracker.exceptions import PersistenceError
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    database = tmp_path / "state.sqlite3"
    subject = service(SQLiteWatchlistRepository(database))
    if kind == "corrupt":
        database.write_bytes(b"corrupt synthetic database")
    else:
        subject.save(record(entry()))
        with sqlite3.connect(database) as connection:
            connection.execute("PRAGMA user_version=99" if kind == "future" else
                               "UPDATE watchlist_entries SET quantity='NaN'")
    before = database.read_bytes()
    for operation in (subject.load, lambda: subject.save(record(entry("OTHER")))):
        with pytest.raises(PersistenceError):
            operation()
        assert database.read_bytes() == before


def test_legacy_adapter_constructor_is_lazy_and_lstat_does_not_follow_targets(tmp_path, monkeypatch):
    from stock_tracker.cli.storage import LegacyFilePresence
    legacy = tmp_path / "opaque.pkl"
    calls = []
    def lstat(path):
        assert path == legacy
        calls.append(path)
        return object()  # An occupied dangling directory entry is sufficient.
    monkeypatch.setattr(Path, "lstat", lstat)
    adapter = LegacyFilePresence(legacy)
    assert calls == []
    assert adapter() is True
    assert calls == [legacy]


def test_legacy_adapter_missing_and_safe_os_failure(tmp_path, monkeypatch):
    from stock_tracker.cli.storage import LegacyFilePresence
    from stock_tracker.exceptions import PersistenceError
    adapter = LegacyFilePresence(tmp_path / "absent.pkl")
    assert adapter() is False
    def fail(path):
        raise PermissionError("sensitive path")
    monkeypatch.setattr(Path, "lstat", fail)
    with pytest.raises(PersistenceError) as caught:
        adapter()
    assert str(caught.value) == "Local storage operation failed."
    assert caught.value.__suppress_context__


def test_real_legacy_entry_blocks_new_namespace_without_open_or_database_create(tmp_path, monkeypatch):
    from stock_tracker.cli.storage import LegacyFilePresence
    from stock_tracker.exceptions import LegacyStatePresentError
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    legacy = tmp_path / "opaque.pkl"
    database = tmp_path / "new.sqlite3"
    legacy.write_bytes(b"untrusted fixture")
    original_open = Path.open
    def guarded(path, *args, **kwargs):
        if path == legacy:
            pytest.fail("Legacy contents opened")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    subject = service(SQLiteWatchlistRepository(database), LegacyFilePresence(legacy))
    for operation in (subject.load, lambda: subject.save(record(entry()))):
        with pytest.raises(LegacyStatePresentError):
            operation()
        assert not database.exists()


def test_shared_result_contract_rejects_unassociated_and_fake_period_invalidation():
    from stock_tracker.exceptions import PersistenceValidationError, ProviderResponseError
    from stock_tracker.services.models import EntryUpdate, PreparedWatchlist
    original = record(entry())
    update = EntryUpdate(0, original.entries[0], None, None, True)
    assert PreparedWatchlist(original, (update,)).updates[0].invalidate_periods
    with pytest.raises(PersistenceValidationError):
        PreparedWatchlist(original, (replace(update, ordinal=1),))
    with pytest.raises(PersistenceValidationError):
        PreparedWatchlist(original, (replace(update, entry=entry("OTHER")),))
    with pytest.raises(ProviderResponseError):
        EntryUpdate(0, original.entries[0], None, object(), True)


@pytest.mark.parametrize("quantity,cost", [(Decimal(-1), Decimal(1)), (Decimal("NaN"), Decimal(1)), (1, Decimal(1))])
def test_shared_ownership_inputs_preserve_numeric_validation(quantity, cost):
    from stock_tracker.domain import DomainValidationError
    from stock_tracker.services.models import OwnershipInput
    with pytest.raises(DomainValidationError):
        OwnershipInput(quantity, cost)
