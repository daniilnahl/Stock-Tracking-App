"""Independent offline M4 transport/cache/SQLite/facade/chart/CLI exit audit.

Run write, read and expired in distinct processes sharing only temporary files.
The HTTP opener is synthetic; the production transport and parser still execute.
"""

import builtins
from contextlib import ExitStack
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
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


root = Path(sys.argv[1]).resolve()
mode = sys.argv[2]
assert mode in {"write", "read", "expired"}
working = Path.cwd().resolve()
sys.path.insert(0, str(root))
if root.name == "src":
    sys.path.insert(1, str(root.parent))


def denied(*args, **kwargs):
    raise AssertionError("External IO denied by historical exit audit")


def proves_denial(operation):
    try:
        operation()
    except AssertionError:
        return
    raise AssertionError("Historical exit guard failed")


real_open, real_io_open, real_connect = builtins.open, io.open, sqlite3.connect


def guarded_open(underlying_open, file, *args, **kwargs):
    if isinstance(file, (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(file)).resolve()
        if path.suffix == ".pkl" or path.name == ".env":
            denied()
        access = args[0] if args else kwargs.get("mode", "r")
        if any(flag in access for flag in "wax+") and not path.is_relative_to(working):
            denied()
    return underlying_open(file, *args, **kwargs)


def guarded_connect(database, *args, **kwargs):
    expected = working / "stock_tracker.sqlite3"
    allowed = {str(expected), expected.as_uri() + "?mode=rw", expected.as_uri() + "?mode=rwc", expected.as_uri() + "?mode=ro"}
    if str(database) not in allowed:
        denied()
    return real_connect(database, *args, **kwargs)


with ExitStack() as guards:
    # Clear inherited credentials before any application import. Dotenv cannot
    # search upward into the checkout; GUI/config output remains temporary.
    environment = {name: os.environ[name] for name in ("SYSTEMROOT", "WINDIR", "PATH") if name in os.environ}
    environment.update(FMP_API_KEY="", MY_API_KEY="", MPLBACKEND="Agg",
                       MPLCONFIGDIR=str(working / "matplotlib"), HOME=str(working),
                       USERPROFILE=str(working), TMP=str(working), TEMP=str(working))
    guards.enter_context(patch.dict(os.environ, environment, clear=True))
    assert os.getenv("FMP_API_KEY") == os.getenv("MY_API_KEY") == ""
    for target, name in (
        (socket, "getaddrinfo"), (socket, "create_connection"),
        (socket.socket, "connect"), (socket.socket, "connect_ex"),
        (socket.socket, "sendto"), (urllib.request, "urlopen"),
        (urllib.request.OpenerDirector, "open"),
        (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps"),
    ):
        guards.enter_context(patch.object(target, name, denied))
        proves_denial(getattr(target, name))
    guards.enter_context(patch.object(builtins, "open", lambda *a, **kw: guarded_open(real_open, *a, **kw)))
    guards.enter_context(patch.object(io, "open", lambda *a, **kw: guarded_open(real_io_open, *a, **kw)))
    guards.enter_context(patch.object(sqlite3, "connect", guarded_connect))
    proves_denial(lambda: Path("watchlist.pkl").read_bytes())
    proves_denial(lambda: Path(".env").read_bytes())
    proves_denial(lambda: sqlite3.connect(working.parent / "outside.sqlite3"))
    proves_denial(lambda: Path(working.parent / "outside.json").write_text("synthetic"))
    import dotenv
    guards.enter_context(patch.object(dotenv, "load_dotenv", lambda *a, **kw: False))
    # Font discovery warns after five wall-clock seconds, including when the
    # host sleeps. Capture that third-party startup diagnostic deterministically.
    font_diagnostics = io.StringIO()
    font_logger = logging.getLogger("matplotlib.font_manager")
    guards.enter_context(patch.object(font_logger, "handlers", [logging.StreamHandler(font_diagnostics)]))
    guards.enter_context(patch.object(font_logger, "propagate", False))

    from stock import Stock
    from watch_list import Watch_list
    from stock_tracker.compatibility import history_operations as history, presentation
    from stock_tracker.compatibility.cli_persistence import save_cli_watchlist
    from stock_tracker.compatibility.watchlist_persistence import watchlist_to_record
    from stock_tracker.persistence.connection import database_connection, transaction
    from stock_tracker.persistence.migrations import SCHEMA_V1, validate_schema
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.providers import factory, transport
    import menu_watchlist as menu
    from typer.testing import CliRunner
    from click.utils import strip_ansi

    guards.enter_context(patch.object(Stock, "graph_performance", denied))
    guards.enter_context(patch.object(Watch_list, "graph_stock", denied))

    base_time = datetime(2020, 1, 7, 12, tzinfo=timezone.utc)
    now = base_time + timedelta(seconds={"write": 0, "read": 3599, "expired": 3600}[mode])
    guards.enter_context(patch.object(history, "utc_now", lambda: now))
    guards.enter_context(patch.object(factory, "datetime", SimpleNamespace(now=lambda tz: now)))
    guards.enter_context(patch.object(factory.time, "monotonic", lambda: 1.0))
    delays = []
    guards.enter_context(patch.object(factory.time, "sleep", delays.append))
    guards.enter_context(patch.object(factory.random, "uniform", lambda a, b: b))
    guards.enter_context(patch.object(presentation.plt, "show", lambda: None))
    guards.enter_context(patch.object(menu, "save_watchlist", denied))
    # Deliberately out-of-order provider observations, no weekend/boundary points,
    # high precision and a raw split-like discontinuity; summary fields disagree.
    payload = (b'[{"symbol":"AAPL","date":"2020-01-06","adjOpen":50,"adjHigh":51,'
               b'"adjLow":49,"adjClose":50.0617283945061728,"volume":null},'
               b'{"symbol":"AAPL","date":"2020-01-02","adjOpen":100,"adjHigh":101,'
               b'"adjLow":99,"adjClose":100.1234567890123456,"volume":0}]')
    calls, closed = [], []
    credential = "synthetic-m4-current-runtime"
    guards.enter_context(patch.object(menu, "API_KEY", credential))

    class Response:
        status = 503 if mode == "expired" else 200
        headers = {}

        def read(self):
            return b"synthetic-sensitive-provider-body" if mode == "expired" else payload

        def close(self):
            closed.append(True)

    class Opener:
        def open(self, request, *, timeout):
            if mode == "read":
                raise AssertionError("Fresh cross-process cache made an HTTP request")
            parts = urlsplit(request.full_url)
            assert parts.scheme == "https" and parts.netloc == "financialmodelingprep.com"
            assert parts.path == "/stable/historical-price-eod/non-split-adjusted"
            assert parse_qs(parts.query) == {"symbol": ["AAPL"], "from": ["2020-01-01"], "to": ["2020-01-06"]}
            assert request.get_method() == "GET" and request.get_header("Apikey") == credential
            assert credential not in request.full_url and timeout == 10.0
            calls.append(request.full_url)
            return Response()

    guards.enter_context(patch.object(transport, "build_opener", lambda *a: Opener()))
    diagnostics = io.StringIO()
    handler = logging.StreamHandler(diagnostics)
    provider_logger = logging.getLogger("stock_tracker.providers.fmp")
    guards.enter_context(patch.object(provider_logger, "handlers", [handler]))
    guards.enter_context(patch.object(provider_logger, "propagate", False))

    database = working / "stock_tracker.sqlite3"
    cache = working / "stock_tracker.history-cache.json"
    repository = SQLiteWatchlistRepository(database)
    if mode == "write":
        assert not database.exists() and not cache.exists()
        previous_credential = "synthetic-old-runtime"
        original = Watch_list("M4 fictional", [Stock("AAPL", previous_credential, exchange="NASDAQ",
            currency="EUR", current_price="120.0000", amount_owned="0.2500", cost_basis="100.0000",
            price_1d="999.99", price_5y="-99.99"), Stock("OTHER", None, exchange="NYSE")])
        save_cli_watchlist(database, menu.WATCHLIST_NAMESPACE, menu.LEGACY_WATCHLIST_FILE, original)
        repository.save(watchlist_to_record(Watch_list("Other CLI", [Stock("KEEP", None)]), "daniils_stock_method"))
        # An existing namespace remains authoritative, but old opaque files must
        # never be read, overwritten or unpickled by graph operations.
        with real_open(working / "watchlist.pkl", "wb") as legacy:
            legacy.write(b"opaque synthetic legacy; do not deserialize")
    database_before = database.read_bytes()
    records_before = [asdict(repository.get(namespace)) for namespace in ("menu_watchlist", "daniils_stock_method")]
    cache_before = cache.read_bytes() if cache.exists() else None
    assert not menu._watchlist_loaded and not menu.current_watchlist.stocks
    runner = CliRunner()
    arguments = ["graph-stock", "--start", "2020-01-01", "--end", "2020-01-06"]
    with patch.object(Stock, "get_price_history", denied):
        result = runner.invoke(menu.app, arguments, input="aapl\n")
    if result.exception is not None and not isinstance(result.exception, SystemExit):
        raise result.exception
    stock, other = menu.current_watchlist.stocks
    assert stock.API_KEY == credential and stock.amount_owned == "0.2500" and stock.cost_basis == "100.0000"
    assert stock.current_price == "120.0000" and stock.price_1d == "999.99" and stock.price_5y == "-99.99"
    assert stock.total_return == "20.0" and other.exchange == "NYSE"
    state_before = dict(stock.__dict__)
    if mode == "expired":
        assert result.exit_code == 1 and "Market-data provider is unavailable." in result.output, result.output
        assert len(calls) == len(closed) == 2 and delays == [0.5]
        assert not presentation.plt.get_fignums()
        assert cache.read_bytes() == cache_before
    else:
        assert result.exit_code == 0, result.output
        expected_dates = [date(2020, 1, 2), date(2020, 1, 6)]
        expected_closes = [Decimal("100.1234567890123456"), Decimal("50.0617283945061728")]
        bars = stock.get_price_history(start=date(2020, 1, 1), end=date(2020, 1, 6))
        assert [bar.date for bar in bars] == expected_dates
        assert [bar.close for bar in bars] == expected_closes
        assert [str(bar.close) for bar in bars] == [str(value) for value in expected_closes]
        assert [bar.volume for bar in bars] == [0, None] and all(bar.adjusted_close is None for bar in bars)
        assert [bar.open for bar in bars] == [Decimal(100), Decimal(50)]
        assert [bar.high for bar in bars] == [Decimal(101), Decimal(51)]
        assert [bar.low for bar in bars] == [Decimal(99), Decimal(49)]
        figure = presentation.plt.gcf()
        axes, = figure.axes
        line, = axes.lines
        assert list(line.get_xdata(orig=True)) == expected_dates
        assert list(line.get_ydata(orig=True)) == [float(value) for value in expected_closes]
        assert line.get_linestyle() == "None" and line.get_marker() == "o"
        assert axes.get_title() == "AAPL — Raw historical close\nRequested: 2020-01-01 to 2020-01-06"
        assert axes.get_ylabel() == "Price (currency unavailable)" and axes.get_xlabel() == "Exchange session date"
        assert figure.texts[0].get_text() == ("Observed: 2020-01-02 to 2020-01-06; 2 observations\n"
                                            "Unadjusted prices; splits may appear as discontinuities.")
        figure.canvas.draw()
        presentation.plt.close("all")
        with patch.object(Stock, "get_price_history", denied):
            repeated = runner.invoke(menu.app, arguments, input="aapl\n")
        assert repeated.exit_code == 0, repeated.output
        presentation.plt.close("all")
        assert len(calls) == len(closed) == (1 if mode == "write" else 0) and not delays
        if mode == "read":
            assert cache.read_bytes() == cache_before

    assert stock.__dict__ == state_before
    assert database.read_bytes() == database_before
    assert [asdict(repository.get(namespace)) for namespace in ("menu_watchlist", "daniils_stock_method")] == records_before
    with database_connection(database) as connection:
        with transaction(connection):
            validate_schema(connection)
            assert connection.execute("PRAGMA user_version").fetchone() == (1,)
            tables = connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name").fetchall()
            assert tables == [(name,) for name in sorted(SCHEMA_V1)]
    document = json.loads(cache.read_text())
    entry, = document["entries"]
    assert document["format"] == "stock-tracker-history-cache" and document["version"] == 1
    assert entry["key"] == dict(provider="fmp", mapping_version="raw-eod-v1", symbol="AAPL",
                                 start="2020-01-01", end="2020-01-06", price_basis="raw")
    assert entry["retrieved_at"] == "2020-01-07T12:00:00.000000+00:00"
    assert [bar["close"] for bar in entry["bars"]] == ["100.1234567890123456", "50.0617283945061728"]
    assert credential.encode() not in database.read_bytes() and credential not in cache.read_text()
    assert b"synthetic-old-runtime" not in database.read_bytes()
    assert credential not in result.output + diagnostics.getvalue()
    assert "synthetic-sensitive-provider-body" not in result.output + diagnostics.getvalue()

    # Input must fail before state loading; identity and missing key must fail
    # before even constructing a cache/provider, including with a fresh cache.
    with patch.object(menu, "_prepare_command", denied):
        invalid = runner.invoke(menu.app, ["graph-stock", "--start", "20200101", "--end", "2020-01-06"])
        assert invalid.exit_code == 1 and invalid.output.strip() == "Historical date range is invalid."
        help_result = runner.invoke(menu.app, ["graph-stock", "--help"], color=True)
        assert help_result.exit_code == 0 and "--start" in strip_ansi(help_result.output)
    with patch.object(factory, "create_historical_market_data_provider", denied):
        with patch.object(menu, "require_api_key", denied):
            unsupported = runner.invoke(menu.app, arguments, input="OTHER\n")
            assert unsupported.exit_code == 1 and "Market data is unavailable." in unsupported.output
        with patch.object(menu, "API_KEY", None):
            missing_key = runner.invoke(menu.app, arguments, input="AAPL\n")
            assert missing_key.exit_code == 1 and "Unable to configure historical market data." in missing_key.output
    assert stock.__dict__ == state_before and not presentation.plt.get_fignums()
    assert database.read_bytes() == database_before
    assert len(calls) == (2 if mode == "expired" else 1 if mode == "write" else 0)
    for name in ("stock_tracker.compatibility.history_operations", "stock_tracker.compatibility.presentation",
                 "stock_tracker.providers.factory", "stock_tracker.providers.fmp", "stock_tracker.providers.transport",
                 "stock_tracker.providers.history_cache", "stock_tracker.persistence.history_cache",
                 "stock_tracker.persistence.sqlite_watchlists"):
        assert Path(sys.modules[name].__file__).resolve().is_relative_to(root)
    facade_root = root.parent if root.name == "src" else root
    for name in ("stock", "watch_list", "menu_watchlist"):
        assert Path(sys.modules[name].__file__).resolve() == facade_root / (name + ".py")
