"""Independent combined M7 audit; synthetic HTTP only, real local API graph."""

import asyncio
import builtins
from contextlib import ExitStack
from dataclasses import replace
from datetime import datetime, timedelta, timezone
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


root, mode = Path(sys.argv[1]).resolve(), sys.argv[2]
assert mode in {"write", "read", "expired"}
working = Path.cwd().resolve()
sys.path.insert(0, str(root))
if root.name == "src":
    sys.path.insert(1, str(root.parent))
# Native Windows asyncio control sockets bootstrap before application denial.
loop = asyncio.new_event_loop()
real_open, real_io_open, real_os_open = builtins.open, io.open, os.open
real_connect = sqlite3.connect
database, cache = working / "holdings.sqlite3", working / "history.json"
legacy_paths = (working / "menu.pkl", working / "evaluation.pkl")
opaque = b"opaque synthetic M7 legacy; never deserialize"
token, key = "synthetic_" * 4, "synthetic-m7-provider"
denials = []


def denied(*args, **kwargs):
    denials.append(True)
    raise AssertionError("M7 external IO denied")


def proves_denial(operation):
    try:
        operation()
    except AssertionError:
        return
    raise AssertionError("M7 denial control did not fire")


def guarded_open(underlying_open, file, *args, **kwargs):
    if isinstance(file, (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(file)).resolve()
        access = args[0] if args else kwargs.get("mode", "r")
        if path in legacy_paths or path.name == ".env":
            denied()
        if any(flag in access for flag in "wax+") and not path.is_relative_to(working):
            denied()
    return underlying_open(file, *args, **kwargs)


def guarded_os_open(file, flags, *args, **kwargs):
    path = Path(os.fsdecode(file)).resolve()
    if path in legacy_paths or path.name == ".env":
        denied()
    if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND) and not path.is_relative_to(working):
        denied()
    return real_os_open(file, flags, *args, **kwargs)


def guarded_connect(path, *args, **kwargs):
    allowed = {str(database), *(database.as_uri() + "?mode=" + value for value in ("ro", "rw", "rwc"))}
    if str(path) not in allowed:
        denied()
    return real_connect(path, *args, **kwargs)


def guarded_move(operation, source, destination, *args, **kwargs):
    if not all(Path(path).resolve().is_relative_to(working) for path in (source, destination)):
        denied()
    return operation(source, destination, *args, **kwargs)


def request(app, path="/health", *, headers=None, query=b""):
    sent = []
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    async def send(message):
        sent.append(message)
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET",
             "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": query,
             "headers": headers if headers is not None else [(b"host", b"127.0.0.1:8000"), (b"authorization", b"Bearer " + token.encode())],
             "root_path": "", "client": ("127.0.0.1", 1), "server": ("127.0.0.1", 8000)}
    loop.run_until_complete(app(scope, receive, send))
    start = next(message for message in sent if message["type"] == "http.response.start")
    assert dict(start["headers"])[b"cache-control"] == b"no-store"
    body = b"".join(message.get("body", b"") for message in sent)
    assert token.encode() not in body and key.encode() not in body and b"sensitive-body" not in body
    return start["status"], json.loads(body)


try:
    with ExitStack() as guards:
        environment = {name: os.environ[name] for name in ("SYSTEMROOT", "WINDIR", "PATH") if name in os.environ}
        environment.update(STOCK_TRACKER_API_TOKEN=token, FMP_API_KEY=key, MY_API_KEY="",
                           HOME=str(working), USERPROFILE=str(working), TMP=str(working), TEMP=str(working))
        guards.enter_context(patch.dict(os.environ, environment, clear=True))
        for target, attribute in ((socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps")):
            guards.enter_context(patch.object(target, attribute, denied))
            proves_denial(getattr(target, attribute))
        guards.enter_context(patch.object(builtins, "open", lambda *a, **k: guarded_open(real_open, *a, **k)))
        guards.enter_context(patch.object(io, "open", lambda *a, **k: guarded_open(real_io_open, *a, **k)))
        guards.enter_context(patch.object(io, "FileIO", denied))
        guards.enter_context(patch.object(os, "open", guarded_os_open))
        real_replace, real_rename = os.replace, os.rename
        guards.enter_context(patch.object(os, "replace", lambda *a, **k: guarded_move(real_replace, *a, **k)))
        guards.enter_context(patch.object(os, "rename", lambda *a, **k: guarded_move(real_rename, *a, **k)))
        guards.enter_context(patch.object(sqlite3, "connect", guarded_connect))
        for legacy in legacy_paths:
            proves_denial(lambda: legacy.read_bytes())
            proves_denial(lambda: os.open(legacy, os.O_RDONLY))
        proves_denial(lambda: (working / ".env").read_bytes())
        proves_denial(lambda: (working.parent / "m7-outside.json").write_text("synthetic"))
        proves_denial(lambda: io.FileIO(working.parent / "m7-outside.json", "w"))
        proves_denial(lambda: os.open(working.parent / "m7-outside.json", os.O_CREAT | os.O_WRONLY))
        proves_denial(lambda: os.replace(cache, working.parent / "m7-outside.json"))
        proves_denial(lambda: os.rename(working.parent / "m7-outside.json", cache))
        proves_denial(lambda: sqlite3.connect(working.parent / "outside.sqlite3"))
        denials.clear()
        import dotenv
        # Explicit process configuration only; never search the user's dotenv.
        guards.enter_context(patch.object(dotenv, "load_dotenv", lambda *a, **k: False))
        from stock_tracker.api import composition
        from stock_tracker.api.configuration import load_api_configuration
        from stock_tracker.domain import Stock
        from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord
        from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
        from stock_tracker.providers import factory, transport
        from stock_tracker.services import history, watchlists
        for module in (composition, history, watchlists, factory, transport):
            assert Path(module.__file__).resolve().is_relative_to(root)

        now = datetime(2020, 1, 7, 12, tzinfo=timezone.utc) + timedelta(seconds={"write": 0, "read": 3599, "expired": 3600}[mode])
        fixed_datetime = SimpleNamespace(now=lambda tz: now)
        guards.enter_context(patch.object(composition, "datetime", fixed_datetime))
        guards.enter_context(patch.object(factory, "datetime", fixed_datetime))
        guards.enter_context(patch.object(factory.time, "monotonic", lambda: 1.0))
        delays, calls, closed = [], [], []
        guards.enter_context(patch.object(factory.time, "sleep", delays.append))
        guards.enter_context(patch.object(factory.random, "uniform", lambda a, b: b))
        payload = (b'[{"symbol":"AAPL","date":"2020-01-06","adjOpen":50,"adjHigh":51,"adjLow":49,'
                   b'"adjClose":50.0617283945061728,"volume":null},'
                   b'{"symbol":"AAPL","date":"2020-01-02","adjOpen":100,"adjHigh":101,"adjLow":99,'
                   b'"adjClose":100.1234567890123456,"volume":9223372036854775807}]')
        class Response:
            status = 503 if mode == "expired" else 200
            headers = {}
            def read(self):
                return b"sensitive-body" if mode == "expired" else payload
            def close(self):
                closed.append(True)
        class Opener:
            def open(self, request, *, timeout):
                assert mode != "read", "Fresh restarted API fetched HTTP"
                parts = urlsplit(request.full_url)
                assert (parts.scheme, parts.netloc, parts.path) == ("https", "financialmodelingprep.com", "/stable/historical-price-eod/non-split-adjusted")
                assert parse_qs(parts.query) == {"symbol": ["AAPL"], "from": ["2020-01-01"], "to": ["2020-01-06"]}
                assert request.get_header("Apikey") == key and key not in request.full_url and timeout == 10.0
                calls.append(True)
                return Response()
        guards.enter_context(patch.object(transport, "build_opener", lambda *a: Opener()))
        diagnostics = io.StringIO()
        for name in ("stock_tracker.api.errors", "stock_tracker.providers.fmp"):
            logger = logging.getLogger(name)
            guards.enter_context(patch.object(logger, "handlers", [logging.StreamHandler(diagnostics)]))
            guards.enter_context(patch.object(logger, "propagate", False))
        repository = SQLiteWatchlistRepository(database)
        namespaces = ("menu_watchlist", "daniils_stock_method")
        if mode == "write":
            entry = WatchlistEntry(Stock("AAPL", name="First", exchange="NASDAQ"), Decimal("0.25"), Decimal("100"), Decimal("80"),
                                  None, None, "opaque USD", None, "999", None, None, None, None, None, None, "-99")
            rows = (entry, replace(entry, stock=Stock("AAPL", name="Second", exchange="NASDAQ")),
                    replace(entry, quantity=Decimal(0), average_cost=None, current_price=Decimal(0)),
                    replace(entry, stock=Stock("AAPL", exchange="NYSE")),
                    replace(entry, quantity=Decimal("0.12345678901234567890123456789"), current_price=None))
            for namespace in namespaces:
                namespaced = tuple(replace(row, stock=replace(row.stock, name=namespace + ":" + (row.stock.name or ""))) for row in rows)
                repository.save(WatchlistRecord(namespace, namespace, namespaced))
            for legacy in legacy_paths:
                with real_open(legacy, "wb") as handle:
                    handle.write(opaque)
        before = database.read_bytes()
        records = tuple(repository.get(namespace) for namespace in namespaces)
        cache_before = cache.read_bytes() if cache.exists() else None
        options = dict(database=str(database), history_cache=str(cache), menu_legacy=str(legacy_paths[0]), evaluation_legacy=str(legacy_paths[1]))
        disabled = composition.create_local_app(load_api_configuration(**options))
        app = composition.create_local_app(load_api_configuration(**options, enable_history=True))
        assert not denials
        with patch.object(sqlite3, "connect", denied), patch.object(factory, "create_historical_market_data_provider", denied):
            proves_denial(lambda: sqlite3.connect(database))
            proves_denial(lambda: factory.create_historical_market_data_provider(key))
            denials.clear()
            assert request(app) == (200, {"status": "ok"})
            assert request(app, "/api/v1/openapi.json")[0] == 200
            assert request(disabled, "/api/v1/watchlists/menu_watchlist/entries/0/history")[1]["error"]["code"] == "history_disabled"
            for headers, expected in (([(b"host", b"127.0.0.1:8000")], 401),
                ([(b"host", b"evil.invalid"), (b"authorization", b"Bearer " + token.encode())], 400),
                ([(b"host", b"127.0.0.1:8000"), (b"authorization", b"Bearer " + token.encode()), (b"origin", b"http://evil.invalid")], 403)):
                assert request(app, "/api/v1/watchlists/menu_watchlist", headers=headers)[0] == expected
        query = b"start=2020-01-01&end=2020-01-06"
        for namespace in namespaces:
            base = "/api/v1/watchlists/" + namespace
            status, view = request(app, base)
            assert status == 200 and view["namespace"] == view["name"] == namespace and view["observation"] == "saved"
            assert view["provenance"] == {"source": None, "observed_at": None, "retrieved_at": None, "freshness": "unknown"}
            entries = view["entries"]
            assert [row["ordinal"] for row in entries] == list(range(5))
            assert [row["stock"]["name"] for row in entries[:2]] == [namespace + ":First", namespace + ":Second"]
            assert entries[0]["snapshot"] == {"cost_basis": "25.00", "market_value": "20.00", "unrealized_pnl": "-5.00", "unrealized_return": "-0.2"}
            assert entries[2]["snapshot"] is None and entries[2]["current_price"] == "0"
            assert entries[4]["quantity"] == "0.12345678901234567890123456789" and entries[4]["snapshot"]["market_value"] is None
            assert request(app, base + "/entries/99/history", query=query)[0] == 404
            assert request(app, base + "/entries/3/history", query=query)[1]["error"]["code"] == "market_data_unavailable"
            assert request(app, base + "/entries/1/history", query=b"start=bad")[0] == 422
            status, result = request(app, base + "/entries/1/history", query=query)
            if mode == "expired":
                assert (status, result) == (503, {"error": {"code": "provider_unavailable", "message": "Market-data provider is unavailable."}})
            else:
                assert status == 200 and result["ordinal"] == 1 and result["stock"]["name"] == namespace + ":Second", (status, result)
                assert result["price_basis"] == "raw" and result["start"] == "2020-01-01" and result["end"] == "2020-01-06"
                assert result["provenance"] == {"source": "fmp", "observed_at": None, "retrieved_at": None, "currency": None, "freshness": "accepted_cache_policy"}
                assert result["bars"] == [dict(symbol="AAPL", date="2020-01-02", open="100", high="101", low="99", close="100.1234567890123456", adjusted_close=None, volume=9223372036854775807),
                                           dict(symbol="AAPL", date="2020-01-06", open="50", high="51", low="49", close="50.0617283945061728", adjusted_close=None, volume=None)]
        assert len(calls) == len(closed) == {"write": 1, "read": 0, "expired": 4}[mode]
        assert delays == ([0.5, 0.5] if mode == "expired" else [])
        assert database.read_bytes() == before and tuple(repository.get(namespace) for namespace in namespaces) == records
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
            assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        for legacy in legacy_paths:
            with real_open(legacy, "rb") as handle:
                assert handle.read() == opaque
        if mode != "write":
            assert cache.read_bytes() == cache_before
        assert set(working.iterdir()) == {database, cache, *legacy_paths}
        assert token not in diagnostics.getvalue() and key not in diagnostics.getvalue() and "sensitive-body" not in diagnostics.getvalue()
        # An application guard violation cannot be hidden by HTTP's safe 500.
        assert not denials
        for name, module in tuple(sys.modules.items()):
            if name == "config" or name == "stock_tracker" or name.startswith("stock_tracker."):
                assert Path(module.__file__).resolve().is_relative_to(root if name != "config" or root.name != "src" else root.parent)
        forbidden = ("stock", "watch_list", "menu_watchlist", "daniils_stock_method", "matplotlib", "rich", "typer",
                     "stock_tracker.cli", "stock_tracker.compatibility")
        assert not any(name == prefix or name.startswith(prefix + ".") for name in sys.modules for prefix in forbidden)
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.run_until_complete(loop.shutdown_default_executor())
    loop.close()
