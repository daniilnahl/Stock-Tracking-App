"""Independent M6 command/service/parser/SQLite/cache audit in fresh processes."""

import builtins
from contextlib import ExitStack
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import io
import json
import logging
import os
from pathlib import Path
import pickle
import socket
import sqlite3
import sys
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import urllib.request


TARGET, MODE = Path(sys.argv[1]).resolve(), sys.argv[2]
assert MODE in {"write", "read", "failures"}
sys.path.insert(0, str(TARGET))
if TARGET.name == "src":
    sys.path.insert(1, str(TARGET.parent))
WORKING = Path.cwd().resolve()
DATABASE = WORKING / "stock_tracker.sqlite3"
CACHE = WORKING / "stock_tracker.history-cache.json"
RUNTIME = "synthetic-m6-audit-runtime"
QUANTITY = "0.12345678901234567890123456789"
COST = "100.12345678901234567890123456789"
SYMBOLS = ["AAPL", "PRECISE", "UNOWNED", "ZEROCOST", "AAPL"]
NOW = datetime(2020, 1, 7, 12, tzinfo=timezone.utc) + timedelta(seconds=3600 if MODE == "failures" else 0)
REQUESTS, SERVICE_CALLS = [], []
PRICE, FAILURE = 120, None


def denied(*args, **kwargs):
    raise AssertionError("M6 exit audit denied external or legacy work")


def proves_denial(action):
    try:
        action()
    except AssertionError:
        return
    raise AssertionError("M6 audit guard control did not deny work")


class TerminalInput(io.BytesIO):
    """Model terminal EOF, avoiding Click 8.1's repeated empty test input."""

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


def main():
    global PRICE, FAILURE
    os.environ.pop("FMP_API_KEY", None)
    os.environ.pop("MY_API_KEY", None)
    os.environ.update(MPLBACKEND="Agg", MPLCONFIGDIR=str(WORKING / "matplotlib"), COLUMNS="600")
    real_open, real_io_open, real_connect = builtins.open, io.open, sqlite3.connect
    def guarded_open(underlying, file, *args, **kwargs):
        if isinstance(file, (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(file)).resolve()
            if path.suffix == ".pkl" or path.name == ".env":
                denied()
        return underlying(file, *args, **kwargs)
    def connect(database, *args, **kwargs):
        allowed = {str(DATABASE), *(DATABASE.as_uri() + "?mode=" + mode for mode in ("ro", "rw", "rwc"))}
        assert str(database) in allowed
        return real_connect(database, *args, **kwargs)

    with ExitStack() as guards:
        for target, name in ((socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps")):
            guards.enter_context(patch.object(target, name, denied))
        guards.enter_context(patch.object(builtins, "open", lambda *a, **kw: guarded_open(real_open, *a, **kw)))
        guards.enter_context(patch.object(io, "open", lambda *a, **kw: guarded_open(real_io_open, *a, **kw)))
        guards.enter_context(patch.object(sqlite3, "connect", connect))
        for action in (lambda: socket.getaddrinfo("example.invalid", 443),
                       lambda: urllib.request.urlopen("https://example.invalid"),
                       lambda: pickle.loads(b"untrusted"), lambda: open("watchlist.pkl", "rb"),
                       lambda: sqlite3.connect(":memory:")):
            proves_denial(action)

        import dotenv
        guards.enter_context(patch.object(dotenv, "load_dotenv", lambda *a, **kw: False))
        from stock_tracker.providers import factory
        # Imports/help must not acquire providers, open storage or inspect legacy entries.
        real_lstat = Path.lstat
        def lstat(path):
            if path.name in {"watchlist.pkl", "daniils_stock_methodd.pkl"}:
                denied()
            return real_lstat(path)
        from typer.testing import CliRunner
        runner = CliRunner()
        with patch.object(factory, "create_market_data_provider", denied), \
             patch.object(factory, "create_historical_market_data_provider", denied), \
             patch.object(sqlite3, "connect", denied), patch.object(Path, "lstat", lstat):
            modules = [importlib.import_module(name) for name in ("menu_watchlist", "daniils_stock_method")]
            for module in modules:
                assert module.API_KEY is None and not module.current_watchlist.stocks
                for command in (None, "add-stock", "refresh", "remove-stock", "show-stocks"):
                    result = runner.invoke(module.app, ([command] if command else []) + ["--help"])
                    assert result.exit_code == 0 and "Usage:" in result.output
            assert runner.invoke(modules[0].app, ["graph-stock", "--help"]).exit_code == 0

        from stock import Stock
        from watch_list import Watch_list
        from stock_tracker.compatibility import history_operations, presentation
        from stock_tracker.domain import Portfolio
        from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
        from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
        from stock_tracker.providers.transport import HttpResponse
        from stock_tracker.services.current_data import CurrentDataService
        from stock_tracker.services.history import HistoryService
        from stock_tracker.services.watchlists import WatchlistService
        diagnostics = io.StringIO()
        provider_logger = logging.getLogger("stock_tracker.providers.fmp")
        guards.enter_context(patch.object(provider_logger, "handlers", [logging.StreamHandler(diagnostics)]))
        guards.enter_context(patch.object(provider_logger, "propagate", False))
        for cls, names in ((CurrentDataService, ("prepare_add", "validate_ownership", "finish_add", "refresh")),
                           (WatchlistService, ("load", "save", "view", "remove")), (HistoryService, ("history",))):
            for name in names:
                original = getattr(cls, name)
                def spy(self, *a, _name=name, _original=original, **kw):
                    SERVICE_CALLS.append(_name)
                    return _original(self, *a, **kw)
                guards.enter_context(patch.object(cls, name, spy))
        for name in ("get_stock_info", "get_price_over_time", "get_price_history", "graph_performance"):
            guards.enter_context(patch.object(Stock, name, denied))
        for name in ("refresh_stocks", "graph_stock", "check_stock_existance"):
            guards.enter_context(patch.object(Watch_list, name, denied))
        guards.enter_context(patch.object(factory, "datetime", SimpleNamespace(now=lambda tz: NOW)))
        guards.enter_context(patch.object(factory.time, "monotonic", lambda: 1.0))
        guards.enter_context(patch.object(factory.time, "sleep", denied))
        guards.enter_context(patch.object(history_operations, "utc_now", lambda: NOW))
        guards.enter_context(patch.object(presentation.plt, "show", lambda: None))

        def transport(url, *, headers, timeout_seconds):
            assert headers == {"apikey": RUNTIME} and timeout_seconds == 10.0 and RUNTIME not in url
            route = urlsplit(url).path.removeprefix("/stable/")
            query = parse_qs(urlsplit(url).query)
            symbol = query.get("symbol", query.get("query"))[0]
            REQUESTS.append((route, symbol))
            if MODE == "read":
                denied()  # A fresh exact cache must satisfy graph requests.
            if FAILURE == "programming":
                raise RuntimeError("Synthetic audit programming failure")
            if route == FAILURE:
                return HttpResponse(403, {}, b"synthetic-private-provider-body")
            if route == "search-symbol":
                body = [] if symbol == "REJECT" else [{"symbol": symbol, "exchange": "NASDAQ"}]
            elif route == "profile":
                body = [{"symbol": symbol, "companyName": "Fictional " + symbol,
                         "exchange": "NASDAQ", "currency": "USD", "price":
                         None if symbol == "UNOWNED" else 0 if symbol == "ZEROCOST" else PRICE,
                         "marketCap": 1000000000}]
            elif route == "stock-price-change":
                return HttpResponse(200, {}, ('[{"symbol":"' + symbol + '","1D":12.345,"5D":-1.235}]').encode())
            else:
                assert route == "historical-price-eod/non-split-adjusted" and symbol == "AAPL"
                assert query == {"symbol": ["AAPL"], "from": ["2020-01-02"], "to": ["2020-01-06"]}
                body = [dict(symbol="AAPL", date=session, adjOpen=price, adjHigh=price,
                             adjLow=price, adjClose=price, volume=0)
                        for session, price in (("2020-01-02", 101.25), ("2020-01-06", 102.5))]
            return HttpResponse(200, {}, json.dumps(body).encode())
        guards.enter_context(patch.object(factory, "UrllibHttpTransport", lambda: SimpleNamespace(get=transport)))
        repository = SQLiteWatchlistRepository(DATABASE)
        portfolios = SQLitePortfolioRepository(DATABASE)

        def invoke(module, args, text="", code=0):
            result = runner.invoke(module.app, args, input=text, terminal_width=600)
            assert result.exit_code == code, (args, result.output, repr(result.exception))
            assert RUNTIME not in result.output and "synthetic-private-provider-body" not in result.output
            return result

        if MODE == "write":
            portfolios.create(Portfolio(88, "Untouched separate portfolio"))
            for module in modules:
                PRICE = 120
                module.API_KEY = RUNTIME
                refs = module.current_watchlist.stocks
                for symbol, quantity, cost in (("AAPL", ".2500", "100.0000"),
                    ("PRECISE", QUANTITY, COST), ("UNOWNED", "0.0000", "-"), ("ZEROCOST", "0.0000", "0.00")):
                    before = len(REQUESTS)
                    invoke(module, ["add-stock"], f"{symbol}\n{quantity}\n{cost}\n")
                    assert REQUESTS[before:] == [(route, symbol) for route in ("search-symbol", "profile", "stock-price-change")]
                assert refs is module.current_watchlist.stocks
                first = refs[0]
                assert (first._snapshot.cost_basis, first._snapshot.market_value, first._snapshot.unrealized_pnl,
                        first._snapshot.unrealized_return) == (Decimal(25), Decimal(30), Decimal(5), Decimal(".2"))
                saved = DATABASE.read_bytes()
                for symbol, message in (("AAPL", "Stock already exists"), ("REJECT", "Invalid ticker")):
                    before = len(REQUESTS)
                    assert message in invoke(module, ["add-stock"], symbol + "\n").output
                    assert REQUESTS[before:] == [("search-symbol", symbol)] and DATABASE.read_bytes() == saved
                aborted = runner.invoke(module.app, ["add-stock"], input=TerminalInput(b"NEW\n"))
                assert aborted.exit_code != 0 and "Succesfully" not in aborted.output
                assert DATABASE.read_bytes() == saved and len(refs) == 4
                PRICE = 126
                before = len(REQUESTS)
                invoke(module, ["refresh"])
                assert REQUESTS[before:] == [(route, symbol) for symbol in SYMBOLS[:4] for route in ("profile", "stock-price-change")]
                assert refs[0] is first and first._snapshot.unrealized_return == Decimal(".26")
                refs[1].price_1d, refs[1].price_5d = "", "[bold]literal[/bold]"
                refs.append(module.load_watchlist().stocks[0])  # Independent equal security occurrence.
                refs.append(Stock("REMOVE", None))
                invoke(module, ["remove-stock"], "REMOVE\n")
                module.current_watchlist.name = module.WATCHLIST_NAMESPACE + " audit"
                module.save_watchlist(module.current_watchlist)
                with real_open(module.LEGACY_WATCHLIST_FILE, "wb") as legacy:
                    legacy.write(b"opaque M6 legacy fixture")
                saved = DATABASE.read_bytes()
                shown = invoke(module, ["show-stocks"]).output
                assert "Average Cost per Share" in shown and "Unrealized Return" in shown
                assert "[bold]literal[/bold]" in shown and DATABASE.read_bytes() == saved

        original = DATABASE.read_bytes()
        for module in modules:
            record = repository.get(module.WATCHLIST_NAMESPACE)
            assert [entry.stock.symbol for entry in record.entries] == SYMBOLS
            assert str(record.entries[1].quantity) == QUANTITY and str(record.entries[1].average_cost) == COST
            assert record.entries[2].average_cost is None and record.entries[2].current_price is None
            assert str(record.entries[3].quantity) == "0.0000" and str(record.entries[3].average_cost) == "0.00"
            assert record.entries[3].current_price == 0 and record.entries[0].current_price == 126
            assert record.entries[1].price_1d == "" and record.entries[1].price_5d == "[bold]literal[/bold]"
            if MODE == "read":
                invoke(module, ["show-stocks"])
                assert all(facade.API_KEY is None for facade in module.current_watchlist.stocks)
                assert DATABASE.read_bytes() == original and not REQUESTS
            elif MODE == "failures":
                module.API_KEY = RUNTIME
                for failure in ("profile", "stock-price-change", "programming"):
                    restored = module.load_watchlist()
                    module.current_watchlist.stocks[:] = restored.stocks
                    module._watchlist_loaded = True
                    states = [dict(stock.__dict__) for stock in restored.stocks]
                    FAILURE, PRICE = failure, 130
                    before = len(REQUESTS)
                    result = invoke(module, ["refresh"], code=1)
                    assert "Succesfully" not in result.output and DATABASE.read_bytes() == original
                    first = module.current_watchlist.stocks[0]
                    assert first.amount_owned == "0.2500" and first.cost_basis == "100.0000"
                    if failure == "programming":
                        assert isinstance(result.exception, RuntimeError) and first.__dict__ == states[0]
                    elif failure == "profile":
                        assert "Market-data provider access was denied." in result.output
                        assert first.current_price is None and first.name == states[0]["name"]
                    else:
                        assert "Market-data provider access was denied." in result.output
                        assert first.current_price == "130" and first.market_cap == "1.000B"
                        assert first.price_1d == first.price_5y == "N/A"
                    assert all(stock.__dict__ == state for stock, state in zip(restored.stocks[1:], states[1:]))
                    assert [route for route, _ in REQUESTS[before:]] == (["profile", "stock-price-change"]
                        if failure == "stock-price-change" else ["profile"])
                FAILURE = None

        menu = modules[0]
        menu.API_KEY = RUNTIME
        if not menu.current_watchlist.stocks:
            menu.current_watchlist.stocks[:] = menu.load_watchlist().stocks
            menu._watchlist_loaded = True
        states = [dict(stock.__dict__) for stock in menu.current_watchlist.stocks]
        cache_before = CACHE.read_bytes() if CACHE.exists() else None
        before = len(REQUESTS)
        if MODE == "failures":
            FAILURE = "historical-price-eod/non-split-adjusted"
        # Two matching AAPL rows retain their order; the second consumes the exact cache.
        result = invoke(menu, ["graph-stock", "--start", "2020-01-02", "--end", "2020-01-06"],
                        "AAPL\n", code=1 if MODE == "failures" else 0)
        assert all(stock.__dict__ == state for stock, state in zip(menu.current_watchlist.stocks, states))
        if MODE == "failures":
            assert "Market-data provider access was denied." in result.output
            assert CACHE.read_bytes() == cache_before and not presentation.plt.get_fignums()
        else:
            axes = presentation.plt.gca()
            assert list(axes.lines[0].get_xdata(orig=True)) == [date(2020, 1, 2), date(2020, 1, 6)]
            assert list(axes.lines[0].get_ydata()) == [101.25, 102.5]
            assert axes.lines[0].get_linestyle() == "None" and axes.get_ylabel() == "Price (currency unavailable)"
            assert "Requested: 2020-01-02 to 2020-01-06" in axes.get_title()
            presentation.plt.close("all")
            if MODE == "read":
                assert CACHE.read_bytes() == cache_before
        assert len(REQUESTS) - before == (0 if MODE == "read" else 1)
        assert DATABASE.read_bytes() == original
        assert portfolios.get(88).name == "Untouched separate portfolio"
        assert RUNTIME.encode() not in original and RUNTIME not in CACHE.read_text(encoding="utf-8")
        for name in ("watchlist.pkl", "daniils_stock_methodd.pkl"):
            with real_open(WORKING / name, "rb") as legacy:
                assert legacy.read() == b"opaque M6 legacy fixture"
        for name, module in tuple(sys.modules.items()):
            if name.startswith("stock_tracker."):
                assert Path(module.__file__).resolve().is_relative_to(TARGET)
        facade_root = TARGET.parent if TARGET.name == "src" else TARGET
        for module in modules:
            assert Path(module.__file__).resolve().parent == facade_root
        required = {"load", "view", "history"} if MODE == "read" else (
            {"load", "save", "view", "remove", "prepare_add", "validate_ownership", "finish_add", "refresh", "history"}
            if MODE == "write" else {"load", "refresh", "history"})
        assert required <= set(SERVICE_CALLS)
        assert RUNTIME not in diagnostics.getvalue() and "synthetic-private-provider-body" not in diagnostics.getvalue()
        if MODE == "failures":
            assert "Market-data request failed." in diagnostics.getvalue()


if __name__ == "__main__":
    main()
