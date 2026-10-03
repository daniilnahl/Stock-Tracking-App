"""Accepted Decimal ownership, immutable replacement and local validation."""

from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext

import pytest


def test_exact_fractional_and_high_precision_inputs():
    from stock_tracker.domain import Position, Stock

    stock = Stock("AAPL")
    quantity = Decimal("0.12345678901234567890123456789")
    average_cost = Decimal("100.12345678901234567890123456789")
    with localcontext() as context:
        context.prec = 3
        position = Position(stock, quantity, average_cost)
    assert position.stock is stock
    assert position.quantity is quantity
    assert position.average_cost is average_cost


@pytest.mark.parametrize("quantity,average_cost", [
    ("0", "100"), ("10", "0"), ("0", "0"),
])
def test_zero_inputs_are_valid(quantity, average_cost):
    from stock_tracker.domain import Position, Stock

    position = Position(Stock("AAPL"), Decimal(quantity), Decimal(average_cost))
    assert position.quantity == Decimal(quantity)
    assert position.average_cost == Decimal(average_cost)


@pytest.mark.parametrize("field", ["quantity", "average_cost"])
@pytest.mark.parametrize("invalid", [
    Decimal("-0.01"), Decimal("NaN"), Decimal("sNaN"),
    Decimal("Infinity"), Decimal("-Infinity"),
    "1.25", "malformed-private-input", 1, 1.25, True, None,
])
def test_invalid_numeric_inputs_raise_safe_error(field, invalid):
    from stock_tracker.domain import DomainValidationError, Position, Stock

    values = {"quantity": Decimal("1"), "average_cost": Decimal("2"), field: invalid}
    with pytest.raises(DomainValidationError) as caught:
        Position(Stock("AAPL"), **values)
    assert str(caught.value) == f"{field} must be a finite nonnegative Decimal."


@pytest.mark.parametrize("invalid", [None, "AAPL", object()])
def test_stock_must_be_domain_stock(invalid):
    from stock_tracker.domain import DomainValidationError, Position

    with pytest.raises(DomainValidationError, match="^stock must be a Stock.$"):
        Position(invalid, Decimal("1"), Decimal("2"))


def test_replacement_is_new_and_preserves_per_share_cost():
    from stock_tracker.domain import Position, Stock

    stock = Stock("AAPL")
    original = Position(stock, Decimal("10"), Decimal("100"))
    replacement = original.with_owned_data(Decimal("0.25"), Decimal("120.12345"))
    assert replacement is not original
    assert replacement.stock is stock
    assert (replacement.quantity, replacement.average_cost) == (
        Decimal("0.25"), Decimal("120.12345"),
    )
    assert (original.quantity, original.average_cost) == (Decimal("10"), Decimal("100"))


@pytest.mark.parametrize("quantity,average_cost", [
    (Decimal("-1"), Decimal("500")), (Decimal("500"), Decimal("-1")),
    (Decimal("NaN"), Decimal("500")), (Decimal("500"), "malformed-private-input"),
])
def test_failed_replacement_preserves_both_original_inputs(quantity, average_cost):
    from stock_tracker.domain import DomainValidationError, Position, Stock

    stock = Stock("AAPL")
    original = Position(stock, Decimal("10"), Decimal("100"))
    with pytest.raises(DomainValidationError):
        original.with_owned_data(quantity, average_cost)
    assert original.stock is stock
    assert (original.quantity, original.average_cost) == (Decimal("10"), Decimal("100"))


@pytest.mark.parametrize("field", ["stock", "quantity", "average_cost"])
def test_position_fields_cannot_change_or_be_deleted(field):
    from stock_tracker.domain import Position, Stock

    position = Position(Stock("AAPL"), Decimal("10"), Decimal("100"))
    with pytest.raises(FrozenInstanceError):
        setattr(position, field, None)
    with pytest.raises(FrozenInstanceError):
        delattr(position, field)


def test_instances_have_independent_inputs_and_no_output(capsys):
    from stock_tracker.domain import Position, Stock

    stock = Stock("AAPL")
    first = Position(stock, Decimal("10"), Decimal("100"))
    second = Position(stock, Decimal("2"), Decimal("20"))
    first.with_owned_data(Decimal("3"), Decimal("30"))
    assert (second.quantity, second.average_cost) == (Decimal("2"), Decimal("20"))
    assert capsys.readouterr().out == ""
    assert capsys.readouterr().err == ""
