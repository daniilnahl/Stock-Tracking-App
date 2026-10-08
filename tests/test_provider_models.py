"""Accepted provider types: precise values, explicit missing/time data, no IO."""

from dataclasses import MISSING, FrozenInstanceError, fields, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest


NOW = datetime(2020, 1, 2, 12, tzinfo=timezone.utc)
MODELS = ("identity", "quote", "profile", "periods", "bar")
PERIODS = ("day_1", "day_5", "month_1", "month_3", "month_6", "year_1", "year_3", "year_5")


@pytest.fixture
def cases():
    from stock_tracker.providers import (
        CompanyProfile, InstrumentIdentity, PeriodChanges, PriceBar, Quote,
    )

    return {
        "identity": (InstrumentIdentity, dict(symbol="AAPL", exchange=None, name=None, currency=None)),
        "quote": (Quote, dict(symbol="AAPL", price=Decimal("0"), exchange=None,
                              currency=None, as_of=None, retrieved_at=NOW)),
        "profile": (CompanyProfile, dict(symbol="AAPL", name="Fictional company",
                                         exchange=None, currency=None, sector=None, country=None,
                                         price=None, market_cap=None, as_of=None, retrieved_at=NOW)),
        "periods": (PeriodChanges, dict(symbol="AAPL", **dict.fromkeys(PERIODS),
                                       as_of=None, retrieved_at=NOW)),
        "bar": (PriceBar, dict(symbol="AAPL", date=date(2020, 1, 2), open=Decimal("0"),
                               high=Decimal("1"), low=Decimal("0"), close=Decimal("0"),
                               adjusted_close=None, volume=None)),
    }


@pytest.mark.parametrize("model", MODELS)
def test_explicit_fields_have_no_defaults_and_instances_are_immutable(model, cases):
    constructor, values = cases[model]
    instance = constructor(**values)
    assert [field.name for field in fields(instance)] == list(values)
    assert all(field.default is MISSING and field.default_factory is MISSING
               for field in fields(instance))
    for field in values:
        with pytest.raises(FrozenInstanceError):
            setattr(instance, field, None)
        with pytest.raises(FrozenInstanceError):
            delattr(instance, field)
    assert constructor(**values) == instance
    assert hash(constructor(**values)) == hash(instance)
    with pytest.raises(TypeError):
        constructor()


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("symbol", ["AAPL", "BRK.B", "ABC-1", "123", "^GSPC"])
def test_symbol_preserves_approved_punctuation_without_normalization(model, symbol, cases):
    constructor, values = cases[model]
    assert constructor(**(values | {"symbol": symbol})).symbol == symbol


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("invalid", [None, "", "aapl", " AAPL", "AAPL ", "AA PL",
                                      "AA\tPL", "AA\nPL", "AA\x00PL", "AA\x7fPL",
                                      "AA\x80PL", "AAPL,MSFT", 1, False, []])
def test_symbol_validation_is_safe_and_never_normalizes(model, invalid, cases):
    from stock_tracker.exceptions import ProviderResponseError

    constructor, values = cases[model]
    with pytest.raises(ProviderResponseError) as caught:
        constructor(**(values | {"symbol": invalid}))
    assert str(caught.value) == "Market-data response has invalid symbol."


TEXT_FIELDS = (
    ("identity", "exchange"), ("identity", "name"), ("identity", "currency"),
    ("quote", "exchange"), ("quote", "currency"), ("profile", "name"),
    ("profile", "exchange"), ("profile", "currency"), ("profile", "sector"),
    ("profile", "country"),
)


@pytest.mark.parametrize("model,field", TEXT_FIELDS)
def test_text_is_exact_optional_metadata_without_inference(model, field, cases):
    constructor, values = cases[model]
    instance = constructor(**(values | {field: "unspecified text"}))
    assert getattr(instance, field) == "unspecified text"
    if (model, field) != ("profile", "name"):
        assert getattr(constructor(**(values | {field: None})), field) is None


@pytest.mark.parametrize("model,field", TEXT_FIELDS)
@pytest.mark.parametrize("invalid", ["", " \t", " synthetic-private-input", "x\n", 1, False, []])
def test_text_rejects_invalid_types_and_blank_or_surrounding_whitespace(model, field, invalid, cases):
    from stock_tracker.exceptions import ProviderResponseError

    constructor, values = cases[model]
    with pytest.raises(ProviderResponseError) as caught:
        constructor(**(values | {field: invalid}))
    assert str(caught.value) == f"Market-data response has invalid {field}."
    assert "synthetic-private-input" not in repr(caught.value)


def test_company_name_is_required_but_currency_and_exchange_are_not_inferred(cases):
    from stock_tracker.exceptions import ProviderResponseError

    constructor, values = cases["profile"]
    with pytest.raises(ProviderResponseError, match="invalid name"):
        constructor(**(values | {"name": None}))
    profile = constructor(**(values | {"currency": "usd", "exchange": "nasdaq"}))
    assert (profile.currency, profile.exchange) == ("usd", "nasdaq")


NUMERIC_FIELDS = (
    ("quote", "price"), ("profile", "price"), ("profile", "market_cap"),
    *(("periods", field) for field in PERIODS),
    *(("bar", field) for field in ("open", "high", "low", "close", "adjusted_close")),
)


@pytest.mark.parametrize("model,field", NUMERIC_FIELDS)
@pytest.mark.parametrize("invalid", [1, 1.5, "1.5", False, True,
                                      Decimal("NaN"), Decimal("sNaN"),
                                      Decimal("Infinity"), Decimal("-Infinity")])
def test_numeric_constructor_inputs_require_actual_finite_decimals(model, field, invalid, cases):
    from stock_tracker.exceptions import ProviderResponseError

    constructor, values = cases[model]
    with pytest.raises(ProviderResponseError) as caught:
        constructor(**(values | {field: invalid}))
    assert str(caught.value) == f"Market-data response has invalid {field}."


@pytest.mark.parametrize("model,field", NUMERIC_FIELDS)
def test_numeric_precision_missing_zero_and_sign_contract(model, field, cases):
    from stock_tracker.exceptions import ProviderResponseError

    constructor, values = cases[model]
    precise = Decimal("123.123456789012345678901234567890")
    if model == "bar":
        values = values | dict.fromkeys(("open", "high", "low", "close"), precise)
    assert getattr(constructor(**(values | {field: precise})), field) is precise
    zero_values = values
    if model == "bar":
        zero_values = values | dict.fromkeys(("open", "high", "low", "close"), Decimal("0"))
    assert getattr(constructor(**(zero_values | {field: Decimal("0")})), field) == Decimal("0")
    missing_allowed = model != "bar" or field == "adjusted_close"
    if missing_allowed:
        assert getattr(constructor(**(values | {field: None})), field) is None
    else:
        with pytest.raises(ProviderResponseError):
            constructor(**(values | {field: None}))
    if model == "periods":
        assert getattr(constructor(**(values | {field: Decimal("-12.5")})), field) == Decimal("-12.5")
    else:
        with pytest.raises(ProviderResponseError):
            constructor(**(values | {field: Decimal("-1")}))


TIME_FIELDS = tuple((model, field) for model in ("quote", "profile", "periods")
                    for field in ("as_of", "retrieved_at"))


@pytest.mark.parametrize("model,field", TIME_FIELDS)
@pytest.mark.parametrize("invalid", [datetime(2020, 1, 2), date(2020, 1, 2),
                                      datetime(2020, 1, 2, tzinfo=timezone(timedelta(hours=1))),
                                      datetime(2020, 1, 2, tzinfo=timezone(timedelta(hours=-7))),
                                      "2020-01-02", 1, False])
def test_market_and_receipt_times_reject_naive_nonutc_or_wrong_types(model, field, invalid, cases):
    from stock_tracker.exceptions import ProviderResponseError

    constructor, values = cases[model]
    with pytest.raises(ProviderResponseError, match=f"invalid {field}"):
        constructor(**(values | {field: invalid}))


@pytest.mark.parametrize("model", ["quote", "profile", "periods"])
def test_market_time_can_be_missing_without_fabrication_but_receipt_time_is_required(model, cases):
    from stock_tracker.exceptions import ProviderResponseError

    constructor, values = cases[model]
    instance = constructor(**values)
    assert instance.as_of is None
    assert instance.retrieved_at is NOW
    timestamp = datetime(2020, 1, 1, tzinfo=timezone(timedelta(0), "exchange-zero-offset"))
    assert replace(instance, as_of=timestamp).as_of is timestamp
    with pytest.raises(ProviderResponseError, match="invalid retrieved_at"):
        replace(instance, retrieved_at=None)
    assert instance.as_of is None and instance.retrieved_at is NOW


@pytest.mark.parametrize("field,invalid", [
    ("date", NOW), ("date", "2020-01-02"), ("date", None), ("date", 1),
    ("volume", True), ("volume", False), ("volume", -1), ("volume", 1.0),
    ("volume", Decimal("1")), ("volume", "1"),
])
def test_price_bar_uses_date_only_and_nullable_nonnegative_integer_volume(field, invalid, cases):
    from stock_tracker.exceptions import ProviderResponseError

    constructor, values = cases["bar"]
    with pytest.raises(ProviderResponseError, match=f"invalid {field}"):
        constructor(**(values | {field: invalid}))


def test_price_bar_keeps_session_label_and_raw_adjusted_prices_separate(cases):
    constructor, values = cases["bar"]
    bar = constructor(**(values | {"high": Decimal("100"), "close": Decimal("100"), "adjusted_close": Decimal("50"),
                                  "volume": 0}))
    assert bar.date == date(2020, 1, 2)
    assert (bar.close, bar.adjusted_close, bar.volume) == (Decimal("100"), Decimal("50"), 0)
    assert replace(bar, volume=10).volume == 10
    # Raw OHLC bounds do not compare values across distinct adjustment bases.
    assert bar.high == Decimal("100")


def test_periods_remain_percentage_points_without_rounding_or_history(cases):
    constructor, values = cases["periods"]
    changes = constructor(**(values | {"day_1": Decimal("12.5123456"), "day_5": Decimal("-2.5")}))
    assert changes.day_1 == Decimal("12.5123456")
    assert changes.day_5 == Decimal("-2.5")
    assert changes.year_5 is None
