"""Separate-process real historical composition and restored facade probe."""

import sys
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
import pickle
import socket
import urllib.request
import os

os.environ["MPLBACKEND"] = "Agg"
os.environ["MPLCONFIGDIR"] = str(Path.cwd() / "matplotlib")

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
if root.name == "src":
    sys.path.insert(1, str(root.parent))


def denied(*args, **kwargs):
    raise AssertionError("External IO denied")


with ExitStack() as guards:
    for target, name in ((socket, "getaddrinfo"), (socket, "create_connection"),
                         (socket.socket, "connect"), (socket.socket, "connect_ex"),
                         (socket.socket, "sendto"), (urllib.request, "urlopen"),
                         (urllib.request.OpenerDirector, "open"),
                         (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps")):
        guards.enter_context(patch.object(target, name, denied))
        try:
            getattr(target, name)()
        except AssertionError:
            pass
        else:
            raise AssertionError("Guard failed")
    from datetime import date, datetime, timezone
    from types import SimpleNamespace
    from stock import Stock
    from watch_list import Watch_list
    from stock_tracker.compatibility import history_operations as history
    from stock_tracker.compatibility.watchlist_persistence import watchlist_to_record, record_to_watchlist
    from stock_tracker.providers import factory
    from stock_tracker.providers.transport import HttpResponse
    from stock_tracker.exceptions import MarketDataUnavailableError

    now = datetime(2020, 1, 7, 12, tzinfo=timezone.utc)
    guards.enter_context(patch.object(history, "utc_now", lambda: now))
    guards.enter_context(patch.object(factory, "datetime", SimpleNamespace(now=lambda tz: now)))
    guards.enter_context(patch.object(factory.time, "monotonic", lambda: 1.0))
    calls = []
    payload = b'[{"symbol":"AAPL","date":"2020-01-02","adjOpen":100,"adjHigh":120,"adjLow":99,"adjClose":110.0000,"volume":0}]'
    def get(self, url, *, headers, timeout_seconds):
        if sys.argv[2] == "read":
            raise AssertionError("Cross-process cache missed")
        calls.append(url)
        return HttpResponse(200, {}, payload)
    guards.enter_context(patch.object(factory.UrllibHttpTransport, "get", get))
    credential = "synthetic-history-probe"
    original = Watch_list("probe", [Stock("AAPL", None, exchange="NASDAQ", currency="EUR",
                          current_price="120", amount_owned="0.2500", cost_basis="100.0000")])
    stock = record_to_watchlist(watchlist_to_record(original, "menu_watchlist"), credential).stocks[0]
    before = dict(stock.__dict__)
    bars = stock.get_price_history(start=date(2020, 1, 2), end=date(2020, 1, 6))
    assert len(bars) == 1 and str(bars[0].close) == "110.0000" and bars[0].adjusted_close is None
    assert stock.__dict__ == before and len(calls) == (1 if sys.argv[2] == "write" else 0)
    from stock_tracker.compatibility import presentation
    guards.enter_context(patch.object(presentation.plt, "show", lambda: None))
    stock.graph_performance(start=date(2020, 1, 2), end=date(2020, 1, 6))
    figure = presentation.plt.gcf()
    axes, = figure.axes
    line, = axes.lines
    assert list(line.get_xdata(orig=True)) == [date(2020, 1, 2)]
    assert list(line.get_ydata(orig=True)) == [110.0]
    assert line.get_linestyle() == "None" and line.get_marker() == "o"
    assert axes.get_title() == "AAPL — Raw historical close\nRequested: 2020-01-02 to 2020-01-06"
    assert axes.get_ylabel() == "Price (currency unavailable)"
    assert "1 observations" in figure.texts[0].get_text()
    figure.canvas.draw()
    presentation.plt.close(figure)
    assert stock.__dict__ == before and str(bars[0].close) == "110.0000"
    assert len(calls) == (1 if sys.argv[2] == "write" else 0)
    assert credential not in Path("stock_tracker.history-cache.json").read_text()
    stock.exchange = "NYSE"
    stock.API_KEY = None
    try:
        stock.get_price_history()
    except MarketDataUnavailableError:
        pass
    else:
        raise AssertionError("Exchange gate failed")
    for name in ("stock_tracker.compatibility.presentation", "stock_tracker.compatibility.history_operations", "stock_tracker.providers.factory",
                 "stock_tracker.providers.history_cache", "stock_tracker.persistence.history_cache"):
        assert Path(sys.modules[name].__file__).resolve().is_relative_to(root)
    facade_root = root.parent if root.name == "src" else root
    assert Path(sys.modules["stock"].__file__).resolve() == facade_root / "stock.py"
