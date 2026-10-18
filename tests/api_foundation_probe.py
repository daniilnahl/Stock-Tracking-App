"""Cold source/wheel API import and execution with independently proven guards."""

import asyncio
import builtins
from contextlib import ExitStack
import importlib.abc
import io
import json
import os
from pathlib import Path
import pickle
import site
import socket
import sqlite3
import sys
import urllib.request
import zoneinfo  # noqa: F401 -- stdlib timezone/sysconfig bootstrap before environment guards
from unittest.mock import patch


FORBIDDEN = (
    "config", "dotenv", "stock", "watch_list", "menu_watchlist", "daniils_stock_method",
    "utils", "stock_tracker.cli", "stock_tracker.compatibility",
    "rich", "typer", "matplotlib", "stock_tracker.providers.factory",
    "stock_tracker.providers.fmp", "stock_tracker.providers.transport", "stock_tracker.providers.history_cache",
    "stock_tracker.providers.finnhub", "stock_tracker.providers.finnhub_transport",
    "stock_tracker.persistence.connection", "stock_tracker.persistence.sqlite_watchlists",
    "stock_tracker.persistence.sqlite_portfolios", "stock_tracker.persistence.migrations",
    "stock_tracker.persistence.history_cache", "stock_tracker.persistence.transfer",
)


def denied(*args, **kwargs):
    raise AssertionError("API foundation isolation denied infrastructure work")


def forbidden(name):
    return any(name == prefix or name.startswith(prefix + ".") for prefix in FORBIDDEN)


class GuardedImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if forbidden(fullname):
            denied()
        return None


class DeniedEnvironment:
    get = __getitem__ = __iter__ = __contains__ = keys = items = values = denied


class DeniedOutput:
    write = writelines = denied


async def exercise(create_app):
    synthetic_credential = "synthetic_" * 4
    from decimal import Decimal
    from datetime import date, datetime, timezone
    from stock_tracker.api import ApiServices
    from stock_tracker.domain import Stock
    from stock_tracker.persistence.models import WatchlistRecord, WatchlistEntry
    from stock_tracker.services.watchlists import WatchlistService
    from stock_tracker.services.history import HistoryService
    from stock_tracker.providers.models import PriceBar
    from stock_tracker.providers.eps import UpcomingEpsEstimate
    from stock_tracker.services.eps import UpcomingEpsService
    calls = []
    class Repository:
        def get(self, namespace):
            calls.append(namespace)
            row = WatchlistEntry(Stock("AAPL", exchange="NASDAQ"), Decimal("10.00"), Decimal("100"), Decimal("120"),
                                 *(None for _ in range(12)))
            return WatchlistRecord(namespace, "Saved", (row, row))
        save = denied
    def acquire(namespace):
        return WatchlistService(Repository(), namespace=namespace, legacy_present=denied)
    history_calls = []
    class Provider:
        def get_price_history(self, symbol, start, end):
            history_calls.append((symbol, start, end))
            return [PriceBar(symbol, date(2020, 2, 29), Decimal("100.00"), Decimal("120"), Decimal("99"),
                             Decimal("110.0000000000000000001"), None, 9223372036854775807)]
    def history_source(ordinal):
        assert ordinal == 1
        return Provider()
    instance = create_app(token=synthetic_credential, services=ApiServices(watchlist=acquire,
        history=HistoryService(history_source, clock=lambda: datetime(2020, 3, 1, tzinfo=timezone.utc)), history_enabled=True))
    assert {route.path for route in instance.routes} == {"/health", "/api/v1/openapi.json", "/api/v1/watchlists/{namespace}", "/api/v1/watchlists/{namespace}/entries/{ordinal}/history", "/api/v1/research/upcoming-eps"}
    for path, authorization in (("/health", []), ("/api/v1/openapi.json", [(b"authorization", b"Bearer " + synthetic_credential.encode())]),
                                ("/api/v1/watchlists/menu_watchlist", [(b"authorization", b"Bearer " + synthetic_credential.encode())]),
                                ("/api/v1/watchlists/daniils_stock_method", [(b"authorization", b"Bearer " + synthetic_credential.encode())]),
                                ("/api/v1/watchlists/menu_watchlist/entries/1/history", [(b"authorization", b"Bearer " + synthetic_credential.encode())])):
        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET",
                 "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"",
                 "headers": [(b"host", b"127.0.0.1:8000"), *authorization], "root_path": "",
                 "client": ("127.0.0.1", 1), "server": ("127.0.0.1", 8000)}
        sent = []
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        async def send(message):
            sent.append(message)
        await instance(scope, receive, send)
        assert sent[0]["status"] == 200
        assert dict(sent[0]["headers"])[b"cache-control"] == b"no-store"
        payload = json.loads(b"".join(item.get("body", b"") for item in sent))
        if path == "/health":
            assert payload == {"status": "ok"} and calls == []
        elif path.endswith("openapi.json"):
            assert payload["paths"].keys() == {"/health", "/api/v1/openapi.json", "/api/v1/watchlists/{namespace}", "/api/v1/watchlists/{namespace}/entries/{ordinal}/history", "/api/v1/research/upcoming-eps"} and calls == []
        elif path.endswith("/history"):
            assert payload["ordinal"] == 1 and payload["start"] == "2015-02-28" and payload["end"] == "2020-02-29"
            assert payload["bars"][0]["close"] == "110.0000000000000000001"
            assert payload["bars"][0]["volume"] == 9223372036854775807
            assert payload["bars"][0]["adjusted_close"] is None
            assert payload["provenance"]["source"] is None and payload["provenance"]["freshness"] == "unknown"
        else:
            assert payload["namespace"] == path.rsplit("/", 1)[1]
            assert [row["ordinal"] for row in payload["entries"]] == [0, 1]
            assert payload["entries"][0]["quantity"] == "10.00"
            assert payload["entries"][0]["snapshot"]["unrealized_return"] == "0.2"
    assert calls == ["menu_watchlist", "daniils_stock_method", "menu_watchlist"]
    assert history_calls == [("AAPL", date(2015, 2, 28), date(2020, 2, 29))]
    eps_calls = []
    class EpsProvider:
        def get_upcoming_eps(self, symbol, **kwargs):
            eps_calls.append((symbol, kwargs))
            return (UpcomingEpsEstimate(symbol, 2026, 3, date(2026, 10, 20), None,
                    Decimal("1.250000000000000001"), datetime(2026, 10, 17, tzinfo=timezone.utc)),)
    service = UpcomingEpsService(lambda: EpsProvider(), research_date=lambda: date(2026, 10, 17))
    eps_path = "/api/v1/research/upcoming-eps"
    scope.update(path=eps_path, raw_path=eps_path.encode(),
                 query_string=b"provider_symbol=TEST&start=2026-10-18&end=2026-10-31")
    sent = []
    from stock_tracker.api import errors as api_errors
    safe_logs = []
    def safe_failure_log(message, code):
        assert message == "API operation failed: %s" and code == "eps_disabled"
        safe_logs.append(code)
    # This failure intentionally emits its fixed category. Capture and validate
    # only this logger call while ordinary output remains denied by the guards.
    with patch.object(api_errors.logger, "warning", safe_failure_log):
        await create_app(token=synthetic_credential, services=ApiServices(upcoming_eps=service))(scope, receive, send)
    assert sent[0]["status"] == 503 and eps_calls == []
    assert safe_logs == ["eps_disabled"]
    sent = []
    await create_app(token=synthetic_credential, services=ApiServices(upcoming_eps=service, upcoming_eps_enabled=True))(scope, receive, send)
    assert sent[0]["status"] == 200
    eps_payload = json.loads(b"".join(item.get("body", b"") for item in sent))
    assert eps_payload["observations"][0]["estimate"] == "1.250000000000000001"
    assert eps_payload["observations"][0]["currency"] is None
    assert eps_payload["date_convention"] == "utc-reference-day/vendor-date-labels"
    assert eps_calls == [("TEST", {"start": date(2026, 10, 18), "end": date(2026, 10, 31), "analysis_date": date(2026, 10, 17)})]
    scope["query_string"] = b""
    # Opt-in construction/health/schema also run under all original cold IO
    # guards. Registering assets must not inspect or open their resources.
    dashboard = create_app(token=synthetic_credential, dashboard=True)
    for path in ("/health", "/api/v1/openapi.json", "/dashboard-assets/unknown"):
        scope["path"] = path
        scope["raw_path"] = path.encode()
        scope["headers"] = [(b"host", b"127.0.0.1:8000"),
            (b"authorization", b"Bearer " + synthetic_credential.encode()),
            (b"origin", b"http://127.0.0.1:8000")]
        sent = []
        await dashboard(scope, receive, send)
        assert sent[0]["status"] == (404 if path.endswith("unknown") else 200)
        assert b"content-security-policy" in dict(sent[0]["headers"])


def main(root, exercise_api=exercise):
    import_root = Path(root).resolve()
    sys.path.insert(0, str(import_root))
    # Native Windows loop bootstrap owns internal control sockets only, before
    # transport guards. No API/framework/service has been imported yet.
    loop = asyncio.new_event_loop()
    original_import = builtins.__import__
    original_open = io.open
    metadata_roots = {Path(path).resolve() for path in (*site.getsitepackages(), str(import_root))}

    def code_metadata_open(file, mode="r", *args, **kwargs):
        candidate = Path(file)
        # Package metadata is part of loading the pinned framework, never user
        # state. Limit reads to distribution metadata under this interpreter.
        if (not any(flag in mode for flag in "wax+") and
                candidate.name in ("METADATA", "entry_points.txt") and
                candidate.parent.name.endswith(".dist-info") and
                candidate.resolve().parent.parent in metadata_roots):
            return original_open(file, mode, *args, **kwargs)
        denied()

    def framework_getenv(key, default=None):
        allowed_callers = {"PYDANTIC_DISABLE_PLUGINS": "pydantic.plugin._loader",
                           "PYDANTIC_VALIDATE_CORE_SCHEMAS": "pydantic._internal._core_utils"}
        if key in allowed_callers and sys._getframe(1).f_globals.get("__name__") == allowed_callers[key]:
            return None  # Default pinned-framework plugin discovery, not credentials.
        denied()

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if not level and forbidden(name):
            denied()
        return original_import(name, globals, locals, fromlist, level)

    try:
        with ExitStack() as guards:
            guards.enter_context(patch.object(sys, "meta_path", [GuardedImports(), *sys.meta_path]))
            guards.enter_context(patch.object(builtins, "__import__", guarded_import))
            for target, attribute in (
                (builtins, "open"), (builtins, "print"), (io, "FileIO"),
                (os, "open"), (os, "read"), (os, "write"),
                (socket, "getaddrinfo"), (socket, "create_connection"),
                (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
                (sqlite3, "connect"), (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
                (pickle, "load"), (pickle, "loads"),
            ):
                guards.enter_context(patch.object(target, attribute, denied))
            guards.enter_context(patch.object(io, "open", code_metadata_open))
            guards.enter_context(patch.object(os, "getenv", framework_getenv))
            guards.enter_context(patch.object(os, "environ", DeniedEnvironment()))
            guards.enter_context(patch.object(sys, "stdout", DeniedOutput()))
            guards.enter_context(patch.object(sys, "stderr", DeniedOutput()))
            probes = (
                lambda: __import__("config"), lambda: __import__("stock_tracker.cli"),
                lambda: __import__("stock_tracker.providers.factory"),
                lambda: __import__("stock_tracker.persistence.sqlite_watchlists"),
                lambda: socket.getaddrinfo("example.invalid", 443),
                lambda: socket.socket().connect(("127.0.0.1", 1)),
                lambda: urllib.request.urlopen("https://example.invalid/"),
                lambda: sqlite3.connect(":memory:"), lambda: pickle.loads(b"opaque synthetic"),
                lambda: os.getenv("STOCK_TRACKER_API_TOKEN"),
                lambda: open("api-foundation-probe", "w"),
                lambda: io.open(Path.cwd() / "fake.dist-info" / "METADATA", "r"),
                lambda: sys.stdout.write("api-foundation-probe"),
            )
            for probe in probes:
                try:
                    probe()
                except (AssertionError, ModuleNotFoundError):
                    pass
                else:
                    raise AssertionError("An API denial control failed")
            from stock_tracker.api import create_app
            from stock_tracker.api import app, serialization, schemas
            for module in (app, serialization, schemas):
                assert Path(module.__file__).resolve().is_relative_to(import_root)
            loop.run_until_complete(exercise_api(create_app))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
        loop.close()


if __name__ == "__main__":
    main(sys.argv[1])
