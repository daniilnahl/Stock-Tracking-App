"""Hand-verifiable position snapshots from the normative FC definitions."""

from dataclasses import FrozenInstanceError
from decimal import Decimal, ROUND_DOWN, localcontext

import pytest


@pytest.mark.parametrize("quantity,cost,price,basis,value,pnl,ratio", [
    ("10", "100", "120", "1000", "1200", "200", "0.20"),
    ("0.25", "100", "120", "25", "30", "5", "0.20"),
    ("10", "100", "80", "1000", "800", "-200", "-0.20"),
    ("10", "100", "0", "1000", "0", "-1000", "-1"),
    ("10", "100", "100", "1000", "1000", "0", "0"),
])
def test_known_value_snapshots(quantity, cost, price, basis, value, pnl, ratio):
    from stock_tracker.domain import Position, Stock
    from stock_tracker.domain.calculations import position_snapshot

    position = Position(Stock("AAPL"), Decimal(quantity), Decimal(cost))
    result = position_snapshot(position, Decimal(price))
    assert (result.cost_basis, result.market_value, result.unrealized_pnl,
            result.unrealized_return) == tuple(Decimal(text) for text in (basis, value, pnl, ratio))
    assert all(isinstance(number, Decimal) for number in (
        result.cost_basis, result.market_value, result.unrealized_pnl, result.unrealized_return,
    ))


@pytest.mark.parametrize("quantity,cost,price,value,pnl", [
    ("0", "100", "120", "0", "0"),
    ("0", "0", "0", "0", "0"),
    ("10", "0", "120", "1200", "1200"),
    ("10", "0", "0", "0", "0"),
])
def test_zero_basis_leaves_return_undefined(quantity, cost, price, value, pnl):
    from stock_tracker.domain import Position, Stock
    from stock_tracker.domain.calculations import position_snapshot

    result = position_snapshot(
        Position(Stock("AAPL"), Decimal(quantity), Decimal(cost)), Decimal(price),
    )
    assert result.cost_basis == Decimal("0")
    assert result.market_value == Decimal(value)
    assert result.unrealized_pnl == Decimal(pnl)
    assert result.unrealized_return is None


@pytest.mark.parametrize("quantity,cost,basis", [
    ("10", "100", "1000"), ("0", "100", "0"), ("10", "0", "0"),
])
def test_missing_price_preserves_basis_and_unavailable_values(quantity, cost, basis):
    from stock_tracker.domain import Position, Stock
    from stock_tracker.domain.calculations import position_snapshot

    result = position_snapshot(Position(Stock("AAPL"), Decimal(quantity), Decimal(cost)), None)
    assert result.cost_basis == Decimal(basis)
    assert result.market_value is None
    assert result.unrealized_pnl is None
    assert result.unrealized_return is None


@pytest.mark.parametrize("invalid", [
    Decimal("-0.01"), Decimal("NaN"), Decimal("sNaN"),
    Decimal("Infinity"), Decimal("-Infinity"),
    "120", "malformed-private-input", 120, 120.0, True, False,
])
def test_invalid_quotes_raise_safe_domain_error(invalid):
    from stock_tracker.domain import DomainValidationError, Position, Stock
    from stock_tracker.domain.calculations import position_snapshot

    position = Position(Stock("AAPL"), Decimal("10"), Decimal("100"))
    with pytest.raises(DomainValidationError) as caught:
        position_snapshot(position, invalid)
    assert str(caught.value) == "current_price must be a finite nonnegative Decimal or None."


@pytest.mark.parametrize("invalid", [None, "private-input", object()])
def test_snapshot_requires_position(invalid):
    from stock_tracker.domain import DomainValidationError
    from stock_tracker.domain.calculations import position_snapshot

    with pytest.raises(DomainValidationError) as caught:
        position_snapshot(invalid, Decimal("120"))
    assert str(caught.value) == "position must be a Position."


def test_precision_has_no_display_quantization_or_context_policy_change():
    from stock_tracker.domain import Position, Stock
    from stock_tracker.domain.calculations import position_snapshot

    quantity = Decimal("0.25")
    cost = Decimal("100.123456")
    price = Decimal("125.154320")
    position = Position(Stock("AAPL"), quantity, cost)
    with localcontext() as context:
        context.prec = 40
        context.rounding = ROUND_DOWN
        result = position_snapshot(position, price)
        assert context.prec == 40
        assert context.rounding == ROUND_DOWN
    # Quarter-share products and their difference are independently hand-derived.
    assert result.cost_basis == Decimal("25.030864")
    assert result.market_value == Decimal("31.288580")
    assert result.unrealized_pnl == Decimal("6.257716")
    assert result.unrealized_return == Decimal("0.25")
    assert position.quantity is quantity and position.average_cost is cost
    assert price == Decimal("125.154320")


def test_each_call_recomputes_without_stale_result_or_input_mutation(capsys):
    from stock_tracker.domain import Position, Stock
    from stock_tracker.domain.calculations import position_snapshot

    position = Position(Stock("AAPL"), Decimal("10"), Decimal("100"))
    original = position_snapshot(position, Decimal("120"))
    missing = position_snapshot(position, None)
    zero_basis = position_snapshot(position.with_owned_data(Decimal("10"), Decimal("0")),
                                   Decimal("120"))
    loss = position_snapshot(position, Decimal("80"))
    repeated = position_snapshot(position, Decimal("120"))
    assert original.unrealized_return == Decimal("0.20")
    assert missing.market_value is None and missing.unrealized_return is None
    assert zero_basis.market_value == Decimal("1200") and zero_basis.unrealized_return is None
    assert loss.unrealized_return == Decimal("-0.20")
    assert repeated == original and repeated is not original
    assert position.quantity == Decimal("10") and position.average_cost == Decimal("100")
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


@pytest.mark.parametrize("field", [
    "cost_basis", "market_value", "unrealized_pnl", "unrealized_return",
])
def test_snapshot_result_is_immutable(field):
    from stock_tracker.domain import Position, Stock
    from stock_tracker.domain.calculations import position_snapshot

    result = position_snapshot(Position(Stock("AAPL"), Decimal("10"), Decimal("100")),
                               Decimal("120"))
    with pytest.raises(FrozenInstanceError):
        setattr(result, field, None)
    with pytest.raises(FrozenInstanceError):
        delattr(result, field)
