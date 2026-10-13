"""Rendered financial labels describe the existing facade values accurately."""

from decimal import Decimal
from io import StringIO

import pytest


@pytest.mark.parametrize("quantity,cost,price,expected_return,expected_basis", [
    ("10", "100", "120", "20.0%", Decimal("1000")),
    ("10", "100", "80", "-20.0%", Decimal("1000")),
    ("0.25", "100.123456789", "120", "19.85%", Decimal("25.03086419725")),
    ("10", "0", "120", "-", Decimal("0")),
    ("10", "100", None, "-", Decimal("1000")),
    ("0", "-", "120", "-", None),
])
def test_rendered_labels_values_and_numeric_state_are_preserved(
    monkeypatch, quantity, cost, price, expected_return, expected_basis,
):
    from rich.console import Console
    from stock import Stock
    import watch_list

    item = Stock("AAPL", None, current_price=price, amount_owned=quantity, cost_basis=cost)
    before = dict(item.__dict__)
    position, snapshot = item._position, item._snapshot
    output = StringIO()
    monkeypatch.setattr(watch_list, "Console", lambda: Console(file=output, width=450, color_system=None))

    watch_list.Watch_list("Example", [item]).show_stocks()

    rendered = output.getvalue()
    assert "Average Cost per Share" in rendered
    assert "Unrealized Return" in rendered
    assert "Cost Basis" not in rendered
    assert "Your Total Return" not in rendered
    row = next(line for line in rendered.splitlines() if "AAPL" in line)
    cells = [cell.strip() for cell in row.split("│")[1:-1]]
    assert cells[4:8] == [quantity, cost, price or "", expected_return]
    assert item.__dict__ == before
    assert item._position is position and item._snapshot is snapshot
    if position is not None:
        assert position.quantity == Decimal(quantity)
        assert position.average_cost == Decimal(cost)
        assert snapshot.cost_basis == expected_basis
        if quantity == "10" and cost == "100" and price == "120":
            assert snapshot.unrealized_return == Decimal("0.20")
