"""Hand-derived single-currency snapshot values and accepted boundary behavior."""

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

import pytest


def row(quantity="10", cost="100", price="120", *, symbol="A", exchange="NASDAQ",
        cost_currency="USD", quote_currency="USD"):
    from stock_tracker.domain import Position, PositionValuationInput, Stock
    return PositionValuationInput(
        Position(Stock(symbol, exchange=exchange), Decimal(quantity), Decimal(cost)),
        None if price is None else Decimal(price), cost_currency, quote_currency,
    )


@pytest.mark.parametrize("prices,value,pnl,ratio,weights", [
    (("120", "60"), "1500", "300", "0.25", ("0.8", "0.2")),
    (("80", "32"), "960", "-240", "-0.2", ("0.8333333333333333333333333333", "0.1666666666666666666666666667")),
    (("0", "0"), "0", "-1200", "-1", (None, None)),
    (("120", None), None, None, None, (None, None)),
    (("0", "60"), "300", "-900", "-0.75", ("0", "1")),
])
def test_known_totals_and_ordered_weights(prices, value, pnl, ratio, weights):
    from stock_tracker.domain import portfolio_snapshot
    inputs = (row(price=prices[0]), row("5", "40", prices[1], symbol="B"))
    result = portfolio_snapshot(inputs, currency="USD")
    assert result.currency == "USD"
    assert result.total_cost_basis == Decimal("1200")
    assert (result.total_market_value, result.aggregate_unrealized_pnl,
            result.aggregate_unrealized_return) == tuple(
                None if item is None else Decimal(item) for item in (value, pnl, ratio))
    assert tuple(item.weight for item in result.positions) == tuple(
        None if item is None else Decimal(item) for item in weights)
    assert all(item.input is supplied for item, supplied in zip(result.positions, inputs))
    assert result.positions[0].snapshot.cost_basis == Decimal("1000")
    assert result.positions[1].snapshot.cost_basis == Decimal("200")


def test_fractional_known_values():
    from stock_tracker.domain import portfolio_snapshot
    result = portfolio_snapshot((row("0.25"), row("0.5", "200", "240")), currency="USD")
    assert (result.total_cost_basis, result.total_market_value,
            result.aggregate_unrealized_pnl, result.aggregate_unrealized_return) == (
                Decimal("125"), Decimal("150"), Decimal("25"), Decimal("0.2"))
    assert tuple(item.weight for item in result.positions) == (Decimal("0.2"), Decimal("0.8"))


@pytest.mark.parametrize("inputs,basis,value,pnl,weights", [
    ((), "0", "0", "0", ()),
    (("0", "100", "120"), "0", "0", "0", (None,)),
    (("0", "100", None), "0", None, None, (None,)),
    (("10", "0", "120"), "0", "1200", "1200", ("1",)),
])
def test_empty_zero_basis_and_missing_zero_quantity(inputs, basis, value, pnl, weights):
    from stock_tracker.domain import portfolio_snapshot
    result = portfolio_snapshot(() if not inputs else (row(*inputs),), currency="USD")
    assert result.total_cost_basis == Decimal(basis)
    assert result.total_market_value == (None if value is None else Decimal(value))
    assert result.aggregate_unrealized_pnl == (None if pnl is None else Decimal(pnl))
    assert result.aggregate_unrealized_return is None
    assert tuple(item.weight for item in result.positions) == tuple(
        None if item is None else Decimal(item) for item in weights)


def test_missing_zero_quantity_row_blocks_other_available_values():
    from stock_tracker.domain import portfolio_snapshot
    result = portfolio_snapshot((row(), row("0", "100", None)), currency="USD")
    assert result.total_cost_basis == Decimal("1000")
    assert result.total_market_value is result.aggregate_unrealized_pnl is None
    assert result.aggregate_unrealized_return is None
    assert tuple(item.weight for item in result.positions) == (None, None)
    assert result.positions[0].snapshot.market_value == Decimal("1200")


def test_order_duplicates_and_unresolved_identity_are_retained():
    from stock_tracker.domain import portfolio_snapshot
    nasdaq, nyse, unknown, another_unknown = row(), row(exchange="NYSE"), row(exchange=None), row(exchange=None)
    equal_known = row(price="60")
    inputs = (nyse, nasdaq, equal_known, nasdaq, unknown, another_unknown)
    result = portfolio_snapshot(inputs, currency="USD")
    assert len(result.positions) == 6
    assert tuple(item.input for item in result.positions) == inputs
    assert all(item.input is supplied for item, supplied in zip(result.positions, inputs))
    assert nasdaq.position.stock == equal_known.position.stock
    assert nasdaq.position.stock != nyse.position.stock
    assert unknown.position.stock != another_unknown.position.stock
    assert result.total_market_value == Decimal("6600")
    assert result.positions[2].snapshot.market_value == Decimal("600")


@pytest.mark.parametrize("field,invalid", [
    ("position", None), ("position", object()),
    *(('current_price', value) for value in (
        "120", 120, 120.0, True, Decimal("-1"), Decimal("NaN"),
        Decimal("sNaN"), Decimal("Infinity"), Decimal("-Infinity"))),
    *((field, value) for field in ("cost_currency", "quote_currency")
      for value in ("", " ", " USD", "USD ", 1, True)),
])
def test_input_rejects_malformed_runtime_fields_without_echo(field, invalid):
    from stock_tracker.domain import DomainValidationError, PositionValuationInput
    valid = row()
    arguments = {item.name: getattr(valid, item.name) for item in fields(valid)}
    arguments[field] = invalid
    with pytest.raises(DomainValidationError) as caught:
        PositionValuationInput(**arguments)
    assert field in str(caught.value)
    assert "120" not in str(caught.value)


@pytest.mark.parametrize("invalid", [None, [], {}, "private-row-input", (None,), (object(),)])
def test_calculation_rejects_non_tuple_or_invalid_rows(invalid):
    from stock_tracker.domain import DomainValidationError, portfolio_snapshot
    with pytest.raises(DomainValidationError):
        portfolio_snapshot(invalid, currency="USD")


@pytest.mark.parametrize("invalid", [None, "", " ", " USD", "USD ", 1, True])
def test_explicit_aggregate_currency_is_required_even_for_empty_rows(invalid):
    from stock_tracker.domain import DomainValidationError, portfolio_snapshot
    with pytest.raises(DomainValidationError, match="currency"):
        portfolio_snapshot((), currency=invalid)


@pytest.mark.parametrize("field", ["cost_currency", "quote_currency"])
@pytest.mark.parametrize("currency,error", [(None, "SnapshotCurrencyUnavailableError"),
                                           ("EUR", "SnapshotCurrencyMismatchError"),
                                           ("usd", "SnapshotCurrencyMismatchError")])
@pytest.mark.parametrize("quantity,price", [("10", "120"), ("0", "120"), ("0", None)])
def test_currency_evidence_is_exact_and_required_for_every_row(field, currency, error, quantity, price):
    import stock_tracker.domain as domain
    invalid = row(quantity, price=price, **{field: currency})
    with pytest.raises(getattr(domain, error)) as caught:
        domain.portfolio_snapshot((row(), invalid), currency="USD")
    assert issubclass(getattr(domain, error), domain.DomainValidationError)
    assert f"Row 1 {field}" in str(caught.value)
    assert "EUR" not in str(caught.value) and "usd" not in str(caught.value)


def test_all_structural_inputs_validated_before_currency_checks_or_arithmetic(monkeypatch):
    from stock_tracker.domain import DomainValidationError, portfolio_snapshot
    from stock_tracker.domain import analytics
    def denied(*args, **kwargs):
        pytest.fail("calculation reached before complete validation")
    monkeypatch.setattr(analytics, "position_snapshot", denied)
    tampered = row()
    object.__setattr__(tampered, "current_price", "private-invalid-price")
    with pytest.raises(DomainValidationError, match="current_price"):
        portfolio_snapshot((row(cost_currency=None), tampered), currency="USD")
    with pytest.raises(DomainValidationError, match="cost_currency is unavailable"):
        portfolio_snapshot((row(cost_currency=None, quote_currency="EUR"),), currency="USD")
    with pytest.raises(DomainValidationError, match="cost_currency does not match"):
        portfolio_snapshot((row(cost_currency="EUR"), row(cost_currency=None)), currency="USD")


@pytest.mark.parametrize("field,invalid", [("position", None), ("cost_currency", " USD"),
                                           ("quote_currency", 1)])
def test_calculation_revalidates_row_fields(field, invalid):
    from stock_tracker.domain import DomainValidationError, portfolio_snapshot
    tampered = row()
    object.__setattr__(tampered, field, invalid)
    with pytest.raises(DomainValidationError, match=field):
        portfolio_snapshot((tampered,), currency="USD")


def test_precision_and_repeating_weights_use_unchanged_caller_context():
    from stock_tracker.domain import portfolio_snapshot
    with localcontext() as context:
        context.prec = 40
        context.rounding = ROUND_DOWN
        inputs = (row("0.25", "100.123456", "125.154320"),) * 3
        result = portfolio_snapshot(inputs, currency="USD")
        assert result.total_cost_basis == Decimal("75.092592")
        assert result.total_market_value == Decimal("93.865740")
        assert result.aggregate_unrealized_pnl == Decimal("18.773148")
        assert result.aggregate_unrealized_return == Decimal("0.25")
        assert all(item.weight == Decimal("0." + "3" * 40) for item in result.positions)
        assert context.prec == 40 and context.rounding == ROUND_DOWN
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        with pytest.raises(Inexact):
            portfolio_snapshot((row("1", "3", "4"),), currency="USD")


def test_each_call_recomputes_without_mutating_inputs_or_printing(capsys):
    from stock_tracker.domain import portfolio_snapshot
    inputs = (row(), row("5", "40", "60"))
    before = tuple((item.position.quantity, item.position.average_cost, item.current_price,
                    item.cost_currency, item.quote_currency) for item in inputs)
    first = portfolio_snapshot(inputs, currency="USD")
    missing = portfolio_snapshot((inputs[0], row("5", "40", None)), currency="USD")
    repeated = portfolio_snapshot(inputs, currency="USD")
    assert repeated == first and repeated is not first
    assert all(a is not b for a, b in zip(first.positions, repeated.positions))
    assert missing.total_market_value is None and first.total_market_value == Decimal("1500")
    assert before == tuple((item.position.quantity, item.position.average_cost, item.current_price,
                            item.cost_currency, item.quote_currency) for item in inputs)
    for instance in (inputs[0], first, first.positions[0]):
        assert not hasattr(instance, "__dict__")
        for field in fields(instance):
            with pytest.raises(FrozenInstanceError):
                setattr(instance, field.name, None)
    assert capsys.readouterr() == ("", "")
