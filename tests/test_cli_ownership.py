"""Legacy CLI ownership flows with real domain arithmetic and controlled HTTP."""

from decimal import Decimal
import io
import json
import pickle
import runpy
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parents[1]


class TerminalInput(io.BytesIO):
    """Model real terminal EOF; Click 8.1 CliRunner otherwise repeats empty input."""

    def read1(self, size=-1):
        chunk = super().read1(size)
        if size != 0 and chunk == b"":
            raise EOFError
        return chunk

    def readline(self, *args):
        line = super().readline(*args)
        if line == b"":
            raise EOFError
        return line


@pytest.fixture(params=["menu_watchlist.py", "daniils_stock_method.py"])
def cli(request, monkeypatch, tmp_path):
    from utils import utility_module

    monkeypatch.setenv("FMP_API_KEY", "synthetic-cli-runtime")
    monkeypatch.setenv("COLUMNS", "300")
    (tmp_path / "list_of_valid_tickers.csv").write_text("", encoding="utf-8")
    provider = {"price": 120, "missing_payload": False, "calls": []}

    def transport(url, **kwargs):
        endpoint = urlsplit(url).path.split("/api/v3/")[1].split("/")[0]
        provider["calls"].append(endpoint)
        if endpoint == "search-ticker":
            payload = [{"symbol": "AAPL"}]
        elif endpoint == "profile":
            payload = [] if provider["missing_payload"] else [{
                "price": provider["price"], "mktCap": 1_000_000_000,
                "companyName": "Fictional company", "sector": "Tech", "country": "US",
                "exchange": "NASDAQ", "currency": "USD",
            }]
        elif endpoint == "stock-price-change":
            payload = [{period: 0 for period in ("1D", "5D", "1M", "3M", "6M", "1Y", "3Y", "5Y")}]
        else:
            pytest.fail("Unexpected provider endpoint")
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(utility_module, "urlopen", transport)
    module = runpy.run_path(str(ROOT / request.param), run_name="ownership_test")
    assert module["WATCHLIST_FILE"] == (
        "watchlist.pkl" if request.param == "menu_watchlist.py" else "daniils_stock_methodd.pkl"
    )
    return module, provider, tmp_path


def add(cli, quantity="0.25", cost="100"):
    module, _, _ = cli
    return CliRunner().invoke(module["app"], ["add-stock"], input=f"aapl\n{quantity}\n{cost}\n")


def test_add_preserves_high_precision_inputs_in_memory_and_saved_state(cli):
    module, provider, directory = cli
    quantity = "0.12345678901234567890123456789"
    cost = "100.12345678901234567890123456789"
    result = add(cli, quantity, cost)
    assert result.exit_code == 0, result.output
    assert "average cost per share" in result.output
    item = module["current_watchlist"].stocks[0]
    assert item._position.quantity == Decimal(quantity)
    assert item._position.average_cost == Decimal(cost)
    encoded = (directory / module["WATCHLIST_FILE"]).read_bytes()
    restored = pickle.loads(encoded).stocks[0]
    assert restored._position.quantity == Decimal(quantity)
    assert restored._position.average_cost == Decimal(cost)
    assert b"synthetic-cli-runtime" not in encoded
    assert provider["calls"] == ["search-ticker", "profile", "stock-price-change"]


@pytest.mark.parametrize("quantity,cost", [("0.25", "100"), ("0", "100"), ("10", "0"), ("0", "0")])
def test_known_values_and_zero_basis_display_without_mutating_numbers(cli, quantity, cost):
    module, _, _ = cli
    assert add(cli, quantity, cost).exit_code == 0
    item = module["current_watchlist"].stocks[0]
    position, snapshot = item._position, item._snapshot
    if quantity == "0.25":
        assert (snapshot.cost_basis, snapshot.market_value, snapshot.unrealized_pnl,
                snapshot.unrealized_return) == (
            Decimal("25"), Decimal("30"), Decimal("5"), Decimal("0.20"),
        )
        assert item.total_return == "20.0"
    else:
        assert snapshot.unrealized_return is None
        assert item.total_return == "-"
    displayed = CliRunner().invoke(module["app"], ["show-stocks"], terminal_width=300)
    assert displayed.exit_code == 0, displayed.output
    assert "AAPL" in displayed.output
    assert item._position is position and item._snapshot is snapshot
    assert item._position.quantity == Decimal(quantity)
    assert item._position.average_cost == Decimal(cost)


@pytest.mark.parametrize("field", ["quantity", "cost"])
@pytest.mark.parametrize("invalid", ["-1", "malformed-private-input", "1_0", "NaN", "Infinity"])
def test_invalid_input_reprompts_then_saves_only_valid_pair(cli, field, invalid):
    module, provider, directory = cli
    quantity, cost = (invalid, "500") if field == "quantity" else ("500", invalid)
    result = CliRunner().invoke(module["app"], ["add-stock"],
                               input=f"aapl\n{quantity}\n{cost}\n0.25\n100\n")
    assert result.exit_code == 0, result.output
    assert "Invalid input." in result.output and "Please try again." in result.output
    assert result.output.count("Enter amount of stocks owned") == 2
    assert len(module["current_watchlist"].stocks) == 1
    item = module["current_watchlist"].stocks[0]
    assert (item._position.quantity, item._position.average_cost) == (Decimal("0.25"), Decimal("100"))
    assert item._snapshot.unrealized_return == Decimal("0.20")
    restored = pickle.loads((directory / module["WATCHLIST_FILE"]).read_bytes())
    assert restored.stocks[0].amount_owned == "0.25" and restored.stocks[0].cost_basis == "100"
    assert provider["calls"] == ["search-ticker", "profile", "stock-price-change"]


@pytest.mark.parametrize("field", ["quantity", "cost"])
def test_aborting_after_invalid_pair_does_not_add_or_save(cli, field):
    module, _, directory = cli
    quantity, cost = ("-1", "500") if field == "quantity" else ("500", "-1")
    stream = TerminalInput(f"aapl\n{quantity}\n{cost}\n".encode())
    result = CliRunner().invoke(module["app"], ["add-stock"], input=stream)
    assert result.exit_code != 0
    assert "Invalid input." in result.output
    assert module["current_watchlist"].stocks == []
    assert not (directory / module["WATCHLIST_FILE"]).exists()


@pytest.mark.parametrize("missing_payload", [True, False])
def test_refresh_missing_quote_replaces_return_and_display_preserves_state(cli, missing_payload):
    module, provider, directory = cli
    assert add(cli).exit_code == 0
    item = module["current_watchlist"].stocks[0]
    assert item._snapshot.unrealized_return == Decimal("0.20")
    provider["price"] = None
    provider["missing_payload"] = missing_payload
    result = CliRunner().invoke(module["app"], ["refresh"])
    assert result.exit_code == 0, result.output
    assert item.current_price == ("N/A" if missing_payload else None)
    assert item._snapshot.cost_basis == Decimal("25")
    assert item._snapshot.market_value is None and item._snapshot.unrealized_return is None
    assert item.total_return == "-"
    position, snapshot = item._position, item._snapshot
    shown = CliRunner().invoke(module["app"], ["show-stocks"], terminal_width=300)
    assert shown.exit_code == 0, shown.output
    assert "AAPL" in shown.output
    if missing_payload:
        assert "N/A" in shown.output
    assert item._position is position and item._snapshot is snapshot
    restored = pickle.loads((directory / module["WATCHLIST_FILE"]).read_bytes()).stocks[0]
    assert restored._position.quantity == Decimal("0.25") and restored.total_return == "-"
    assert provider["calls"] == [
        "search-ticker", "profile", "stock-price-change", "profile", "stock-price-change",
    ]


def test_duplicate_and_remove_preserve_existing_behavior(cli):
    module, provider, directory = cli
    assert add(cli).exit_code == 0
    encoded = (directory / module["WATCHLIST_FILE"]).read_bytes()
    duplicate = CliRunner().invoke(module["app"], ["add-stock"], input="aapl\n")
    assert duplicate.exit_code == 0
    assert "Stock already exists in the watchlist." in duplicate.output
    assert (directory / module["WATCHLIST_FILE"]).read_bytes() == encoded
    assert provider["calls"] == ["search-ticker", "profile", "stock-price-change"]
    removed = CliRunner().invoke(module["app"], ["remove-stock"], input="aapl\n")
    assert removed.exit_code == 0
    assert module["current_watchlist"].stocks == []
    assert pickle.loads((directory / module["WATCHLIST_FILE"]).read_bytes()).stocks == []


def test_exponent_inputs_reach_domain_without_float_roundtrip(cli):
    module, _, _ = cli
    result = add(cli, "2.5e-1", "1e2")
    assert result.exit_code == 0, result.output
    item = module["current_watchlist"].stocks[0]
    assert item._position.quantity == Decimal("0.25")
    assert item._position.average_cost == Decimal("100")
    assert item._snapshot.unrealized_return == Decimal("0.20")


def test_unowned_watchlist_entry_stays_unowned_through_display_and_save(cli):
    module, _, directory = cli
    result = add(cli, "0", "-")
    assert result.exit_code == 0, result.output
    item = module["current_watchlist"].stocks[0]
    assert item._position is None and item._snapshot is None
    assert (item.amount_owned, item.cost_basis, item.total_return) == ("0", "-", "-")
    shown = CliRunner().invoke(module["app"], ["show-stocks"])
    assert shown.exit_code == 0, shown.output
    assert item._position is None
    restored = pickle.loads((directory / module["WATCHLIST_FILE"]).read_bytes()).stocks[0]
    assert restored._position is None and restored.cost_basis == "-"


@pytest.mark.parametrize("field", ["quantity", "cost"])
def test_aborted_invalid_add_preserves_existing_list_and_file(cli, field):
    module, _, directory = cli
    assert add(cli).exit_code == 0
    item = module["current_watchlist"].stocks[0]
    before = (directory / module["WATCHLIST_FILE"]).read_bytes()
    quantity, cost = ("-1", "500") if field == "quantity" else ("500", "-1")
    stream = TerminalInput(f"msft\n{quantity}\n{cost}\n".encode())
    result = CliRunner().invoke(module["app"], ["add-stock"], input=stream)
    assert result.exit_code != 0 and "Invalid input." in result.output
    assert module["current_watchlist"].stocks == [item]
    assert module["current_watchlist"].stocks[0] is item
    assert (directory / module["WATCHLIST_FILE"]).read_bytes() == before
    assert item._position.quantity == Decimal("0.25") and item._position.average_cost == Decimal("100")
