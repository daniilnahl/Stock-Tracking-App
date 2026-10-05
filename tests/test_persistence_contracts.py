"""Accepted storage records and capabilities; no concrete persistence required."""

from dataclasses import MISSING, FrozenInstanceError, fields, replace
from decimal import Decimal, localcontext
import inspect
from pathlib import Path
import subprocess
import sys
from typing import get_type_hints

import pytest

METADATA = (
    "sector", "country", "currency", "market_cap", "price_1d", "price_5d", "price_30d",
    "price_3m", "price_6m", "price_1y", "price_3y", "price_5y",
)


def entry(**changes):
    from stock_tracker.domain import Stock
    from stock_tracker.persistence import WatchlistEntry

    return WatchlistEntry(**(dict(stock=Stock("aapl"), quantity=Decimal("0"),
                                 average_cost=None, current_price=None,
                                 **dict.fromkeys(METADATA)) | changes))


def test_records_have_exact_required_fields_and_are_frozen():
    from stock_tracker.persistence import WatchlistRecord

    item = entry()
    record = WatchlistRecord("menu_watchlist", "Watchlist", (item,))
    assert [field.name for field in fields(item)] == [
        "stock", "quantity", "average_cost", "current_price", *METADATA,
    ]
    assert [field.name for field in fields(record)] == ["namespace", "name", "entries"]
    for instance in (item, record):
        for field in fields(instance):
            assert field.default is MISSING and field.default_factory is MISSING
            with pytest.raises(FrozenInstanceError):
                setattr(instance, field.name, None)
            with pytest.raises(FrozenInstanceError):
                delattr(instance, field.name)
        with pytest.raises(TypeError):
            type(instance)()


@pytest.mark.parametrize("field", ["quantity", "average_cost", "current_price"])
@pytest.mark.parametrize("invalid", [True, False, 0, 1.5, "0", [], Decimal("-1"),
                                      Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"),
                                      Decimal("-Infinity")])
def test_numeric_input_rejects_types_negative_and_nonfinite_safely(field, invalid):
    from stock_tracker.exceptions import PersistenceValidationError

    with pytest.raises(PersistenceValidationError) as caught:
        entry(**{field: invalid})
    assert str(caught.value) == "Local storage input is invalid."


def test_required_quantity_and_stock_and_missing_nonzero_cost_fail():
    from stock_tracker.exceptions import PersistenceValidationError

    for changes in ({"quantity": None}, {"stock": None}, {"stock": "synthetic-private"},
                    {"quantity": Decimal("0.25"), "average_cost": None}):
        with pytest.raises(PersistenceValidationError):
            entry(**changes)


def test_decimal_inputs_are_exact_without_context_rounding_or_missing_zero_conflation():
    quantity = Decimal("0.123456789012345678901234567890")
    cost = Decimal("123456789.012345678901234567890")
    with localcontext() as context:
        context.prec = 2
        item = entry(quantity=quantity, average_cost=cost, current_price=Decimal("0"))
    assert item.quantity is quantity and item.average_cost is cost
    assert item.quantity.as_tuple() == quantity.as_tuple()
    assert item.average_cost.as_tuple() == cost.as_tuple()
    assert item.current_price == Decimal("0")
    unowned = entry()
    zero_position = entry(average_cost=Decimal("0"), current_price=Decimal("0"))
    assert unowned.average_cost is None and unowned.current_price is None
    assert zero_position.average_cost == zero_position.current_price == Decimal("0")


@pytest.mark.parametrize("field", METADATA)
@pytest.mark.parametrize("value", [None, "", "-", "N/A", "1.5M", "  exact text  ", "-12.5"])
def test_metadata_preserves_display_strings_without_parsing(field, value):
    assert getattr(entry(**{field: value}), field) == value


@pytest.mark.parametrize("field", METADATA)
@pytest.mark.parametrize("invalid", [1, True, Decimal("1"), [], {}])
def test_metadata_rejects_nontext(field, invalid):
    from stock_tracker.exceptions import PersistenceValidationError

    with pytest.raises(PersistenceValidationError):
        entry(**{field: invalid})


@pytest.mark.parametrize("field", ["namespace", "name"])
@pytest.mark.parametrize("invalid", [None, "", " \t", " leading", "trailing ", 1, False, []])
def test_record_names_are_nonblank_exact_text(field, invalid):
    from stock_tracker.exceptions import PersistenceValidationError
    from stock_tracker.persistence import WatchlistRecord

    record = WatchlistRecord("menu_watchlist", "Watchlist", ())
    with pytest.raises(PersistenceValidationError):
        replace(record, **{field: invalid})


@pytest.mark.parametrize("invalid", [None, [], "private", (None,), (object(),)])
def test_entries_require_immutable_tuple_of_valid_records(invalid):
    from stock_tracker.exceptions import PersistenceValidationError
    from stock_tracker.persistence import WatchlistRecord

    with pytest.raises(PersistenceValidationError):
        WatchlistRecord("menu_watchlist", "Watchlist", invalid)


def test_entries_reject_mutable_list_even_with_valid_entry():
    from stock_tracker.exceptions import PersistenceValidationError
    from stock_tracker.persistence import WatchlistRecord

    with pytest.raises(PersistenceValidationError):
        WatchlistRecord("menu_watchlist", "Watchlist", [entry()])


def test_records_preserve_order_duplicates_unknown_identity_and_separate_namespaces():
    from stock_tracker.domain import Stock
    from stock_tracker.persistence import WatchlistRecord

    nasdaq = entry(stock=Stock("aapl", exchange="NASDAQ"))
    equal_identity = entry(stock=Stock("aapl", name="Other", exchange="NASDAQ"))
    nyse = entry(stock=Stock("aapl", exchange="NYSE"))
    unknown = entry()
    another_unknown = entry()
    entries = (nyse, nasdaq, equal_identity, nasdaq, unknown, another_unknown)
    record = WatchlistRecord("menu_watchlist", "Watchlist", entries)
    other = WatchlistRecord("daniils_stock_method", "Watchlist", ())
    assert record.entries is entries and other.entries == ()
    assert all(actual is expected for actual, expected in zip(record.entries, entries))
    assert nasdaq.stock == equal_identity.stock and nasdaq.stock != nyse.stock
    assert unknown.stock != another_unknown.stock
    assert nasdaq.stock.symbol == "aapl"


@pytest.mark.parametrize("name,message", [
    ("PersistenceError", "Local storage operation failed."),
    ("PersistenceValidationError", "Local storage input is invalid."),
    ("PersistenceDataError", "Local storage data is invalid."),
    ("PersistenceConflictError", "Local storage record already exists."),
    ("PersistenceNotFoundError", "Local storage record was not found."),
    ("SchemaVersionError", "Local storage schema is unsupported."),
    ("LegacyStatePresentError", "Legacy state requires an explicit safe transition before saving."),
])
def test_errors_have_distinct_safe_fixed_no_argument_contracts(name, message):
    from stock_tracker import exceptions

    constructor = getattr(exceptions, name)
    error = constructor()
    assert isinstance(error, exceptions.PersistenceError)
    assert isinstance(error, exceptions.StockTrackerError)
    assert str(error) == message and error.args == (message,)
    assert repr(error) == f"{name}({message!r})"
    with pytest.raises(TypeError) as caught:
        constructor("synthetic-private-input")
    assert "synthetic-private-input" not in str(caught.value)


def test_protocols_expose_only_accepted_signatures_and_typed_results():
    from stock_tracker.domain import Portfolio
    from stock_tracker.persistence import PortfolioRepository, WatchlistRecord, WatchlistRepository

    expected = {
        PortfolioRepository: {
            "create": ("portfolio", Portfolio, Portfolio),
            "get": ("portfolio_id", int, Portfolio | None),
            "list": (None, None, list[Portfolio]),
            "save": ("portfolio", Portfolio, type(None)),
            "delete": ("portfolio_id", int, bool),
        },
        WatchlistRepository: {
            "get": ("namespace", str, WatchlistRecord | None),
            "list": (None, None, list[WatchlistRecord]),
            "save": ("record", WatchlistRecord, type(None)),
        },
    }
    for protocol, methods in expected.items():
        assert {name for name in protocol.__dict__ if not name.startswith("_")} == set(methods)
        for method, (parameter, annotation, result) in methods.items():
            function = getattr(protocol, method)
            assert list(inspect.signature(function).parameters) == (
                ["self"] if parameter is None else ["self", parameter]
            )
            hints = get_type_hints(function)
            assert hints == ({"return": result} if parameter is None
                             else {parameter: annotation, "return": result})


def test_source_imports_and_construction_need_no_infrastructure(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", str(root / "tests" / "persistence_contract_probe.py"),
         str(root / "src")], cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []
