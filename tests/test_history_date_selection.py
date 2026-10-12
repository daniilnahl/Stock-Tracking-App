"""Deterministic CLI range selection through real history/cache/render boundaries."""

from datetime import date, datetime, timezone
import importlib
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner


@pytest.fixture
def rig(monkeypatch):
    from stock import Stock
    from stock_tracker.compatibility import history_operations as history, presentation
    from stock_tracker.providers import factory
    from stock_tracker.providers.transport import HttpResponse
    module = importlib.reload(importlib.import_module("menu_watchlist"))
    credential = "synthetic-old"
    stock = Stock("AAPL", credential, exchange="NASDAQ", amount_owned="0.2500", cost_basis="100")
    module.current_watchlist.stocks[:] = [stock]
    module._watchlist_loaded = True
    monkeypatch.setattr(module, "API_KEY", "synthetic-current")
    now = datetime(2020, 3, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(history, "utc_now", lambda: now)
    monkeypatch.setattr(factory, "datetime", SimpleNamespace(now=lambda tz: now))
    monkeypatch.setattr(presentation.plt, "show", lambda: None)
    monkeypatch.setattr(module, "save_watchlist", lambda *a: pytest.fail("Graph saved holdings"))
    calls = []
    def get(self, url, *, headers, timeout_seconds):
        calls.append((url, headers))
        return HttpResponse(200, {}, b'[{"symbol":"AAPL","date":"2020-01-02","adjOpen":100,"adjHigh":120,"adjLow":99,"adjClose":110,"volume":0}]')
    monkeypatch.setattr(factory.UrllibHttpTransport, "get", get)
    presentation.plt.close("all")
    yield SimpleNamespace(module=module, stock=stock, calls=calls, plt=presentation.plt, factory=factory)
    presentation.plt.close("all")


@pytest.mark.parametrize("options,interval", [([], "2015-02-28 to 2020-02-29"),
    (["--start", "2020-01-02", "--end", "2020-01-06"], "2020-01-02 to 2020-01-06")])
def test_real_cli_history_request_plot_cache_and_runtime_restoration(rig, options, interval):
    before = dict(rig.stock.__dict__)
    runner = CliRunner()
    for _ in range(2):
        result = runner.invoke(rig.module.app, ["graph-stock", *options], input="aapl\n")
        assert result.exit_code == 0, result.output
        axes = rig.plt.gca()
        assert axes.get_title().endswith(interval)
        assert list(axes.lines[0].get_xdata(orig=True)) == [date(2020, 1, 2)]
        assert list(axes.lines[0].get_ydata()) == [110.0]
        assert rig.stock.__dict__ == before
        rig.plt.close("all")
    assert len(rig.calls) == 1
    assert rig.calls[0][1] == {"apikey": "synthetic-current"}
    from pathlib import Path
    assert not Path("stock_tracker.sqlite3").exists()


@pytest.mark.parametrize("options", [["--start", "2020-01-02"], ["--end", "2020-01-06"],
    ["--start", "20200102", "--end", "2020-01-06"],
    ["--start", "2020-02-30", "--end", "2020-01-06"],
    ["--start", "2020-01-06", "--end", "2020-01-02"],
    ["--start", "2020-01-02", "--end", "2020-03-01"],
    ["--start", "2000-01-01", "--end", "2020-01-06"]])
def test_invalid_options_fail_before_state_factory_or_cache(rig, monkeypatch, options):
    monkeypatch.setattr(rig.module, "_prepare_command", lambda *a, **kw: pytest.fail("State preflight"))
    result = CliRunner().invoke(rig.module.app, ["graph-stock", *options])
    assert result.exit_code == 1
    assert result.output.strip() == "Historical date range is invalid."
    assert not rig.calls and not rig.plt.get_fignums()


@pytest.mark.parametrize("exchange", [None, "N/A", "NYSE", "nasdaq", "XNAS", "NASDAQ "])
def test_exchange_gate_before_key_precheck(rig, monkeypatch, exchange):
    rig.stock.exchange = exchange
    monkeypatch.setattr(rig.module, "require_api_key", lambda *a: pytest.fail("Key preflight"))
    result = CliRunner().invoke(rig.module.app, ["graph-stock"], input="AAPL\n")
    assert result.exit_code == 1 and "Market data is unavailable." in result.output
    assert not rig.calls and not rig.plt.get_fignums()


def test_missing_ticker_no_key_or_history(rig, monkeypatch):
    monkeypatch.setattr(rig.module, "require_api_key", lambda *a: pytest.fail("Key preflight"))
    result = CliRunner().invoke(rig.module.app, ["graph-stock"], input="MISSING\n")
    assert result.exit_code == 0 and not rig.calls


@pytest.mark.parametrize("error_name", ["ConfigurationError", "HistoryCacheError", "ProviderTimeoutError", "RuntimeError",
    "MarketDataUnavailableError", "ProviderResponseError", "ProviderUnavailableError", "RateLimitError",
    "ProviderAccessError", "ProviderAuthenticationError", "ProviderRequestError"])
def test_errors_safe_and_runtime_key_restored(rig, monkeypatch, error_name):
    from config import ConfigurationError
    from stock_tracker import exceptions
    error = ConfigurationError("synthetic-sensitive") if error_name == "ConfigurationError" else (
        RuntimeError("programming failure") if error_name == "RuntimeError" else getattr(exceptions, error_name)())
    def failed(*a):
        raise error
    monkeypatch.setattr(rig.factory, "create_historical_market_data_provider", failed)
    before = dict(rig.stock.__dict__)
    result = CliRunner().invoke(rig.module.app, ["graph-stock"], input="AAPL\n")
    assert result.exit_code == 1 and rig.stock.__dict__ == before
    if error_name == "RuntimeError":
        assert result.exception is error
    else:
        assert "synthetic-sensitive" not in result.output
        assert ("Unable to configure historical market data." if error_name == "ConfigurationError" else str(error)) in result.output
    assert not rig.plt.get_fignums()


def test_missing_runtime_key_precheck_before_factory(rig, monkeypatch):
    monkeypatch.setattr(rig.module, "API_KEY", None)
    before = dict(rig.stock.__dict__)
    result = CliRunner().invoke(rig.module.app, ["graph-stock"], input="AAPL\n")
    assert result.exit_code == 1 and "Unable to configure historical market data." in result.output
    assert not rig.calls and rig.stock.__dict__ == before


@pytest.mark.parametrize("exchange", ["NASDAQ", "NYSE"])
def test_real_sqlite_restore_graph_current_runtime_key_and_gate(rig, monkeypatch, exchange):
    rig.stock.exchange = exchange
    # Persist via the real command's repository boundary, then emulate restart.
    from stock_tracker.compatibility.cli_persistence import save_cli_watchlist
    save_cli_watchlist(rig.module.WATCHLIST_FILE, rig.module.WATCHLIST_NAMESPACE,
                      rig.module.LEGACY_WATCHLIST_FILE, rig.module.current_watchlist)
    before_database = rig.module.WATCHLIST_FILE.read_bytes()
    rig.module.current_watchlist.stocks.clear()
    rig.module._watchlist_loaded = False
    if exchange == "NYSE":
        monkeypatch.setattr(rig.module, "require_api_key", lambda *a: pytest.fail("Identity gate bypassed"))
    result = CliRunner().invoke(rig.module.app,
        ["graph-stock", "--start", "2020-01-02", "--end", "2020-01-06"], input="AAPL\n")
    assert result.exit_code == (0 if exchange == "NASDAQ" else 1), result.output
    restored, = rig.module.current_watchlist.stocks
    assert restored.API_KEY == "synthetic-current"
    assert restored.amount_owned == "0.2500" and restored.cost_basis == "100"
    assert rig.module.WATCHLIST_FILE.read_bytes() == before_database
    assert len(rig.calls) == (1 if exchange == "NASDAQ" else 0)


def test_watchlist_order_duplicates_and_stock_like_default(monkeypatch):
    from watch_list import Watch_list
    from stock_tracker.compatibility import history_operations
    monkeypatch.setattr(history_operations, "utc_now", lambda: datetime(2020, 3, 1, tzinfo=timezone.utc))
    calls = []
    class DefaultOnly:
        ticker_symbol = "AAPL"
        def graph_performance(self):
            calls.append("default")
    Watch_list("default", [DefaultOnly(), DefaultOnly()]).graph_stock("AAPL")
    assert calls == ["default", "default"]
    calls.clear()
    def stock(label, ticker="AAPL"):
        return SimpleNamespace(ticker_symbol=ticker, graph_performance=lambda **kw: calls.append((label, kw)))
    watchlist = Watch_list("explicit", [stock("first"), stock("other", "MSFT"), stock("second")])
    watchlist.graph_stock("AAPL", start=date(2020, 1, 2), end=date(2020, 1, 6))
    assert calls == [(label, {"start": date(2020, 1, 2), "end": date(2020, 1, 6)}) for label in ("first", "second")]
