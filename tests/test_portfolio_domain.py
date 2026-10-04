"""Accepted Portfolio identity, construction validation and list ownership."""

from decimal import Decimal

import pytest


@pytest.mark.parametrize("identifier", [None, 0, 1, -1])
def test_empty_portfolio_preserves_identity(identifier):
    from stock_tracker.domain import Portfolio

    portfolio = Portfolio(identifier, "Example")
    assert portfolio.id == identifier
    assert portfolio.name == "Example"
    assert portfolio.positions == []
    assert isinstance(portfolio.positions, list)


@pytest.mark.parametrize("invalid", [True, False, "1", 1.0, Decimal("1"), object()])
def test_invalid_id_has_safe_error(invalid):
    from stock_tracker.domain import DomainValidationError, Portfolio

    with pytest.raises(DomainValidationError) as caught:
        Portfolio(invalid, "Example")
    assert str(caught.value) == "id must be an int or None."


@pytest.mark.parametrize("invalid", [None, "", " \t\n", " Example", "Example ", 1])
def test_invalid_name_has_safe_error(invalid):
    from stock_tracker.domain import DomainValidationError, Portfolio

    with pytest.raises(DomainValidationError) as caught:
        Portfolio(None, invalid)
    assert str(caught.value) == "name must be a nonblank string without surrounding whitespace."


@pytest.mark.parametrize("invalid", [(), "private-input", {}, 1])
def test_collection_must_be_list_or_none(invalid):
    from stock_tracker.domain import DomainValidationError, Portfolio

    with pytest.raises(DomainValidationError) as caught:
        Portfolio(None, "Example", invalid)
    assert str(caught.value) == "positions must be a list of Position instances or None."


@pytest.mark.parametrize("invalid", [None, "private-input", object()])
def test_collection_elements_are_validated_without_changing_caller_list(invalid):
    from stock_tracker.domain import DomainValidationError, Portfolio, Position, Stock

    position = Position(Stock("AAPL"), Decimal("0.25"), Decimal("100"))
    supplied = [position, invalid]
    with pytest.raises(DomainValidationError) as caught:
        Portfolio(None, "Example", supplied)
    assert str(caught.value) == "positions must contain only Position instances."
    assert supplied[0] is position
    assert supplied[1] is invalid


def test_defaults_and_explicit_none_have_independent_lists():
    from stock_tracker.domain import Portfolio, Position, Stock

    first = Portfolio(None, "First")
    second = Portfolio(None, "Second")
    explicit_none = Portfolio(None, "Third", None)
    position = Position(Stock("AAPL"), Decimal("1"), Decimal("100"))
    first.positions.append(position)
    assert first.positions == [position]
    assert second.positions == []
    assert explicit_none.positions == []
    assert first.positions is not second.positions
    assert second.positions is not explicit_none.positions


def test_constructor_copies_list_but_keeps_position_instances():
    from stock_tracker.domain import Portfolio, Position, Stock

    first = Position(Stock("AAPL"), Decimal("0.25"), Decimal("100.123456"))
    second = Position(Stock("MSFT"), Decimal("2"), Decimal("200"))
    supplied = [first]
    portfolio = Portfolio(7, "Example", supplied)
    other = Portfolio(8, "Other", supplied)
    assert portfolio.positions is not supplied
    assert portfolio.positions[0] is first
    supplied.append(second)
    assert portfolio.positions == [first]
    portfolio.positions.append(second)
    portfolio.positions.remove(first)
    assert portfolio.positions == [second]
    assert other.positions == [first]
    assert supplied == [first, second]
    assert (first.quantity, first.average_cost) == (Decimal("0.25"), Decimal("100.123456"))


def test_order_duplicates_and_exchange_identities_are_not_consolidated(capsys):
    from stock_tracker.domain import Portfolio, Position, Stock

    nasdaq = Position(Stock("AAPL", exchange="NASDAQ"), Decimal("1"), Decimal("100"))
    same_identity = Position(Stock("AAPL", exchange="NASDAQ"), Decimal("1"), Decimal("100"))
    nyse = Position(Stock("AAPL", exchange="NYSE"), Decimal("1"), Decimal("100"))
    unknown = Position(Stock("AAPL"), Decimal("1"), Decimal("100"))
    another_unknown = Position(Stock("AAPL"), Decimal("1"), Decimal("100"))
    supplied = [nyse, nasdaq, same_identity, nasdaq, unknown, another_unknown]
    portfolio = Portfolio(None, "Example", supplied)
    assert len(portfolio.positions) == len(supplied)
    assert all(actual is expected for actual, expected in zip(portfolio.positions, supplied))
    assert nasdaq.stock == same_identity.stock
    assert nasdaq.stock != nyse.stock
    assert unknown.stock != another_unknown.stock
    assert capsys.readouterr() == ("", "")
