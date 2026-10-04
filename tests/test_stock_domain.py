"""Accepted local Stock identity and infrastructure isolation contracts."""

from dataclasses import FrozenInstanceError, fields

import pytest


def test_stock_required_optional_fields_and_exact_spelling():
    from stock_tracker.domain import Stock

    stock = Stock("brk.b", name="Berkshire Hathaway", exchange="NYSE")
    assert (stock.symbol, stock.name, stock.exchange) == (
        "brk.b", "Berkshire Hathaway", "NYSE",
    )
    assert [field.name for field in fields(stock)] == ["symbol", "name", "exchange"]
    assert Stock("AAPL").name is None
    assert Stock("AAPL").exchange is None


@pytest.mark.parametrize("field", ["symbol", "name", "exchange"])
@pytest.mark.parametrize("invalid", ["", " \t", " AAPL", "AAPL\n", 1, False, []])
def test_invalid_fields_raise_safe_local_errors(field, invalid):
    from stock_tracker.domain import DomainValidationError, Stock

    values = {"symbol": "AAPL", field: invalid}
    with pytest.raises(DomainValidationError) as caught:
        Stock(**values)
    assert str(caught.value) == (
        f"{field} must be a nonblank string without surrounding whitespace."
    )


def test_required_symbol_and_safe_error_do_not_echo_input():
    from stock_tracker.domain import DomainValidationError, Stock

    for value in (None, " private-input "):
        with pytest.raises(DomainValidationError) as caught:
            Stock(value)
        assert "private-input" not in str(caught.value)
        assert str(caught.value).startswith("symbol must")


@pytest.mark.parametrize("field", ["symbol", "name", "exchange"])
def test_stock_fields_cannot_change_or_be_deleted(field):
    from stock_tracker.domain import Stock

    stock = Stock("AAPL", name="Apple", exchange="NASDAQ")
    with pytest.raises(FrozenInstanceError):
        setattr(stock, field, "changed")
    with pytest.raises(FrozenInstanceError):
        delattr(stock, field)
    assert (stock.symbol, stock.name, stock.exchange) == ("AAPL", "Apple", "NASDAQ")


def test_known_identity_ignores_name_but_preserves_symbol_and_exchange():
    from stock_tracker.domain import Stock

    first = Stock("AAPL", name="Apple", exchange="NASDAQ")
    renamed = Stock("AAPL", None, "NASDAQ")
    assert first == renamed
    assert renamed == first
    assert hash(first) == hash(renamed) == hash(("AAPL", "NASDAQ"))
    assert len({first, renamed}) == 1
    assert first != Stock("AAPL", exchange="NYSE")
    assert first != Stock("aapl", exchange="NASDAQ")
    assert first != Stock("AAPL", exchange="nasdaq")
    assert first != "AAPL"


def test_unknown_identity_is_reflexive_and_distinct_from_other_instances():
    from stock_tracker.domain import Stock

    first = Stock("AAPL")
    second = Stock("AAPL")
    known = Stock("AAPL", exchange="NASDAQ")
    assert first == first
    assert first != second
    assert second != first
    assert first != known
    assert known != first
    assert hash(first) == object.__hash__(first)
    assert hash(second) == object.__hash__(second)
    assert len({first, second, known}) == 3
    assert {first: "unresolved"}[first] == "unresolved"
