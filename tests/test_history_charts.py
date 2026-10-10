"""Real Agg plot data and safe rendering of accepted historical observations."""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

START, END = date(2020, 1, 2), date(2020, 1, 6)


def bar(session=START, close="110.123456789123456789"):
    from stock_tracker.providers.models import PriceBar
    value = Decimal(close)
    return PriceBar("AAPL", session, value, value, value, value, None, 0)


@pytest.fixture
def rig(monkeypatch, tmp_path):
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    import matplotlib
    matplotlib.use("Agg", force=True)
    from stock import Stock
    from stock_tracker.compatibility import history_operations as history, presentation
    from stock_tracker.providers import factory
    import socket
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **kw: pytest.fail("Network reached"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(history, "utc_now", lambda: datetime(2020, 3, 1, tzinfo=timezone.utc))
    monkeypatch.setattr(presentation.plt, "show", lambda: None)
    credential = "synthetic-chart"
    stock = Stock("AAPL", credential, exchange="NASDAQ", currency="USD",
                  current_price=None, price_1d="not-a-number", price_5y=None,
                  amount_owned="0.2500", cost_basis="100.0000")
    result = SimpleNamespace(stock=stock, history=history, factory=factory, plt=presentation.plt,
                             bars=[bar(), bar(END, "0")], calls=[])
    def get(symbol, start, end):
        result.calls.append((symbol, start, end))
        return result.bars
    monkeypatch.setattr(factory, "create_historical_market_data_provider",
                        lambda key: SimpleNamespace(get_price_history=get))
    result.plt.close("all")
    yield result
    result.plt.close("all")


def test_actual_sparse_dates_raw_precision_labels_and_no_state_mutation(rig):
    before = dict(rig.stock.__dict__)
    assert rig.stock.graph_performance(start=START, end=END) is None
    figure = rig.plt.gcf()
    axes, = figure.axes
    line, = axes.lines
    assert list(line.get_xdata(orig=True)) == [START, END]
    assert list(line.get_ydata(orig=True)) == [float(Decimal("110.123456789123456789")), 0.0]
    assert line.get_linestyle() == "None" and line.get_marker() == "o"
    assert axes.get_title() == "AAPL — Raw historical close\nRequested: 2020-01-02 to 2020-01-06"
    assert axes.get_ylabel() == "Price (currency unavailable)"
    assert figure.texts[0].get_text() == (
        "Observed: 2020-01-02 to 2020-01-06; 2 observations\n"
        "Unadjusted prices; splits may appear as discontinuities.")
    assert rig.stock.__dict__ == before
    assert str(rig.bars[0].close) == "110.123456789123456789"
    assert rig.calls == [("AAPL", START, END)]
    figure.canvas.draw()


def test_default_resolves_once_with_changing_clock_and_carries_request_labels(rig, monkeypatch):
    calls = []
    def clock():
        calls.append(1)
        return datetime(2020, 3, len(calls), tzinfo=timezone.utc)
    monkeypatch.setattr(rig.history, "utc_now", clock)
    rig.stock.graph_performance()
    assert len(calls) == 1
    assert rig.calls == [("AAPL", date(2015, 2, 28), date(2020, 2, 29))]
    assert rig.plt.gca().get_title().endswith("Requested: 2015-02-28 to 2020-02-29")


def test_single_observation_is_single_marker(rig):
    rig.bars = [bar()]
    rig.stock.graph_performance(start=START, end=END)
    line, = rig.plt.gca().lines
    assert list(line.get_xdata(orig=True)) == [START]
    assert len(line.get_ydata()) == 1 and line.get_linestyle() == "None"


@pytest.mark.parametrize("close", ["1e10000", "1e-10000"])
def test_unrenderable_finite_decimal_fails_before_figure_without_mutation(rig, close):
    from stock_tracker.exceptions import MarketDataUnavailableError
    rig.bars = [bar(), bar(END, close)]
    before = dict(rig.stock.__dict__), list(rig.bars)
    with pytest.raises(MarketDataUnavailableError, match="^Market data is unavailable\\.$"):
        rig.stock.graph_performance(start=START, end=END)
    assert rig.plt.get_fignums() == []
    assert rig.stock.__dict__ == before[0] and rig.bars == before[1]


@pytest.mark.parametrize("case", ["empty", "none", "object", "descending", "duplicate"])
def test_empty_and_malformed_history_never_create_figure(rig, case):
    from stock_tracker.exceptions import MarketDataUnavailableError, ProviderResponseError
    rig.bars = {"empty": [], "none": None, "object": [object()],
                "descending": [bar(END), bar()], "duplicate": [bar(), bar()]}[case]
    with pytest.raises((MarketDataUnavailableError, ProviderResponseError)):
        rig.stock.graph_performance(start=START, end=END)
    assert rig.plt.get_fignums() == []


@pytest.mark.parametrize("start,end", [(START, None), (None, END), (True, END),
                                      (END, START), (START, date(2020, 3, 1))])
def test_invalid_graph_range_never_reaches_factory_or_figure(rig, monkeypatch, start, end):
    from stock_tracker.exceptions import HistoryRangeError
    monkeypatch.setattr(rig.factory, "create_historical_market_data_provider",
                        lambda *a: pytest.fail("Invalid range reached factory"))
    with pytest.raises(HistoryRangeError):
        rig.stock.graph_performance(start=start, end=end)
    assert rig.plt.get_fignums() == []


def test_chart_never_reads_current_quote_or_summaries(rig):
    stock_type = type(rig.stock)
    class GuardedStock(stock_type):
        def __getattribute__(self, name):
            if name in {"current_price", "currency", "price_1d", "price_5d", "price_30d",
                        "price_3m", "price_6m", "price_1y", "price_3y", "price_5y"}:
                raise AssertionError("Quote or summary read")
            return super().__getattribute__(name)
    rig.stock.__class__ = GuardedStock
    rig.stock.graph_performance(start=START, end=END)
    assert len(rig.plt.gca().lines[0].get_ydata()) == 2


@pytest.mark.parametrize("exchange", [None, "N/A", "NYSE", "nasdaq", "XNAS", "NASDAQ "])
def test_identity_gate_precedes_clock_key_factory_and_all_plotting(rig, monkeypatch, exchange):
    from stock_tracker.exceptions import MarketDataUnavailableError
    rig.stock.exchange = exchange
    rig.stock.API_KEY = None
    def denied(*a, **kw):
        pytest.fail("Gate reached clock or factory")
    monkeypatch.setattr(rig.history, "utc_now", denied)
    monkeypatch.setattr(rig.factory, "create_historical_market_data_provider", denied)
    with pytest.raises(MarketDataUnavailableError):
        rig.stock.graph_performance()
    assert rig.plt.get_fignums() == []


@pytest.mark.parametrize("error_name", ["ProviderTimeoutError", "HistoryCacheError", "RuntimeError"])
def test_provider_and_programming_errors_propagate_without_figure(rig, monkeypatch, error_name):
    from stock_tracker import exceptions
    error_type = RuntimeError if error_name == "RuntimeError" else getattr(exceptions, error_name)
    def failed(*a, **kw):
        raise error_type()
    monkeypatch.setattr(rig.factory, "create_historical_market_data_provider", failed)
    with pytest.raises(error_type):
        rig.stock.graph_performance(start=START, end=END)
    assert rig.plt.get_fignums() == []
