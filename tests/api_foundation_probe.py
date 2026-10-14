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
    instance = create_app(token=synthetic_credential)
    assert {route.path for route in instance.routes} == {"/health", "/api/v1/openapi.json"}
    for path, authorization in (("/health", []), ("/api/v1/openapi.json", [(b"authorization", b"Bearer " + ("synthetic_" * 4).encode())])):
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
        assert payload == {"status": "ok"} if path == "/health" else payload["paths"].keys() == {"/health", "/api/v1/openapi.json"}


def main(root):
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
            loop.run_until_complete(exercise(create_app))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
        loop.close()


if __name__ == "__main__":
    main(sys.argv[1])
