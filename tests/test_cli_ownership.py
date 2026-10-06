"""Legacy CLI ownership flows with real domain arithmetic and controlled HTTP."""

from decimal import Decimal
from datetime import datetime, timezone
import io
import json
import runpy
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

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
    from stock_tracker.providers import factory
    from stock_tracker.providers.transport import HttpResponse

    monkeypatch.setenv("FMP_API_KEY", "synthetic-cli-runtime")
    monkeypatch.setenv("COLUMNS", "300")
    (tmp_path / "list_of_valid_tickers.csv").write_text("", encoding="utf-8")
    provider = {"price": 120, "missing_payload": False, "calls": []}

    def transport(url, *, headers, timeout_seconds):
        endpoint = urlsplit(url).path.removeprefix('/stable/')
        assert headers == {'apikey': 'synthetic-cli-runtime'}
        query = parse_qs(urlsplit(url).query)
        symbol = query.get('symbol', query.get('query'))[0]
        provider['calls'].append(endpoint)
        if endpoint == 'search-symbol':
            payload = provider.get('lookup_rows', [{'symbol': symbol, 'exchange': 'NASDAQ'}])
        elif endpoint == 'profile':
            payload = [] if provider['missing_payload'] else [{
                'symbol': symbol, 'price': provider['price'], 'marketCap': 1_000_000_000,
                'companyName': 'Fictional company', 'sector': 'Tech', 'country': 'US',
                'exchange': 'NASDAQ', 'currency': 'USD',
            }]
        elif endpoint == 'stock-price-change':
            payload = [dict(symbol=symbol, **{period: 0 for period in ('1D', '5D', '1M', '3M', '6M', '1Y', '3Y', '5Y')})]
        else:
            pytest.fail('Unexpected provider endpoint')
        return HttpResponse(200, {}, json.dumps(payload).encode())

    monkeypatch.setattr(utility_module, 'urlopen', lambda *a, **kw: pytest.fail('Legacy transport reached'))
    monkeypatch.setattr(factory, 'UrllibHttpTransport', lambda: SimpleNamespace(get=transport))
    monkeypatch.setattr(factory, 'datetime', SimpleNamespace(now=lambda tz: datetime(2020, 1, 1, tzinfo=timezone.utc)))
    monkeypatch.setattr(factory.time, 'monotonic', lambda: 0.0)
    module = runpy.run_path(str(ROOT / request.param), run_name="ownership_test")
    assert module["WATCHLIST_FILE"] == tmp_path / "stock_tracker.sqlite3"
    assert module["WATCHLIST_NAMESPACE"] == request.param.removesuffix(".py")
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
    restored = module["load_watchlist"]().stocks[0]
    assert restored._position.quantity == Decimal(quantity)
    assert restored._position.average_cost == Decimal(cost)
    assert b"synthetic-cli-runtime" not in encoded
    assert provider["calls"] == ["search-symbol", "profile", "stock-price-change"]


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
    restored = module["load_watchlist"]()
    assert restored.stocks[0].amount_owned == "0.25" and restored.stocks[0].cost_basis == "100"
    assert provider["calls"] == ["search-symbol", "profile", "stock-price-change"]


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
    before = (directory / module["WATCHLIST_FILE"]).read_bytes()
    result = CliRunner().invoke(module["app"], ["refresh"])
    assert result.exit_code == (1 if missing_payload else 0), result.output
    assert item.current_price is None
    assert item._snapshot.cost_basis == Decimal("25")
    assert item._snapshot.market_value is None and item._snapshot.unrealized_return is None
    assert item.total_return == "-"
    position, snapshot = item._position, item._snapshot
    shown = CliRunner().invoke(module["app"], ["show-stocks"], terminal_width=300)
    assert shown.exit_code == 0, shown.output
    assert "AAPL" in shown.output
    assert item._position is position and item._snapshot is snapshot
    restored = module["load_watchlist"]().stocks[0]
    assert restored._position.quantity == Decimal("0.25")
    assert restored.total_return == ('20.0' if missing_payload else '-')
    if missing_payload:
        assert (directory / module["WATCHLIST_FILE"]).read_bytes() == before
        assert 'Market data is unavailable.' in result.output
    assert provider["calls"] == ['search-symbol', 'profile', 'stock-price-change', 'profile'] + ([] if missing_payload else ['stock-price-change'])


def test_duplicate_and_remove_preserve_existing_behavior(cli):
    module, provider, directory = cli
    assert add(cli).exit_code == 0
    encoded = (directory / module["WATCHLIST_FILE"]).read_bytes()
    duplicate = CliRunner().invoke(module["app"], ["add-stock"], input="aapl\n")
    assert duplicate.exit_code == 0
    assert "Stock already exists in the watchlist." in duplicate.output
    assert (directory / module["WATCHLIST_FILE"]).read_bytes() == encoded
    assert provider["calls"] == ["search-symbol", "profile", "stock-price-change", "search-symbol"]
    removed = CliRunner().invoke(module["app"], ["remove-stock"], input="aapl\n")
    assert removed.exit_code == 0
    assert module["current_watchlist"].stocks == []
    assert module["load_watchlist"]().stocks == []


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
    restored = module["load_watchlist"]().stocks[0]
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


@pytest.mark.parametrize('rows', [[], [{'symbol': 'UNKNOWNX', 'exchange': 'NASDAQ'}]])
def test_scoped_no_match_discards_only_new_candidate_and_preserves_saved_holdings(cli, rows, monkeypatch):
    module, provider, directory = cli
    assert add(cli).exit_code == 0
    assert CliRunner().invoke(module['app'], ['add-stock'], input='msft\n2\n50\n').exit_code == 0
    existing = list(module['current_watchlist'].stocks)
    states = [dict(item.__dict__) for item in existing]
    saved = directory / module['WATCHLIST_FILE']
    before = saved.read_bytes()
    csv = directory / 'list_of_valid_tickers.csv'
    csv.write_bytes(b'UNKNOWN\n')  # A legacy positive must not override lookup.
    provider['calls'].clear()
    provider['lookup_rows'] = rows
    def denied(*args, **kwargs):
        pytest.fail('rejected candidate was constructed or persisted')
    monkeypatch.setitem(module['add_stock'].__globals__, 'Stock', denied)
    monkeypatch.setitem(module['add_stock'].__globals__, 'save_watchlist', denied)
    result = CliRunner().invoke(module['app'], ['add-stock'], input='unknown\n')
    assert result.exit_code == 0 and 'Invalid ticker. Try again.' in result.output
    assert 'Succesfully' not in result.output and 'amount of stocks owned' not in result.output
    assert 'average cost per share' not in result.output
    assert provider['calls'] == ['search-symbol']
    assert module['current_watchlist'].stocks == existing
    assert all(item is old and item.__dict__ == state
               for item, old, state in zip(module['current_watchlist'].stocks, existing, states))
    assert saved.read_bytes() == before and csv.read_bytes() == b'UNKNOWN\n'
