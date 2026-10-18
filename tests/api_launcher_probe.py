"""Cold API help/composition under independently proven source/wheel guards."""

import builtins
from contextlib import ExitStack, redirect_stdout
import io
import json
import logging
import os
from pathlib import Path
import pickle
import socket
import sqlite3
import sys
import urllib.request
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_foundation_probe import denied, DeniedEnvironment, DeniedOutput, forbidden, GuardedImports, main

_configuration = None


def guarded_launch_configuration(*, dashboard=False, upcoming_eps=False):
    """Only synthetic process-token lookup and native path metadata may occur."""
    from stock_tracker.api.configuration import load_api_configuration
    original_import = builtins.__import__
    class LaunchEnvironment(DeniedEnvironment):
        def get(self, key, default=None):
            if key == "STOCK_TRACKER_API_TOKEN":
                return "synthetic_" * 4
            denied()
    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if not level and forbidden(name):
            denied()
        return original_import(name, globals, locals, fromlist, level)
    with ExitStack() as guards:
        guards.enter_context(patch.object(sys, "meta_path", [GuardedImports(), *sys.meta_path]))
        guards.enter_context(patch.object(builtins, "__import__", guarded_import))
        guards.enter_context(patch.object(os, "environ", LaunchEnvironment()))
        for target, attribute in (
            (builtins, "open"), (builtins, "print"), (io, "open"), (io, "FileIO"),
            (os, "open"), (os, "read"), (os, "write"), (os, "getenv"),
            (sqlite3, "connect"), (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (pickle, "load"), (pickle, "loads"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(sys, "stdout", DeniedOutput()))
        guards.enter_context(patch.object(sys, "stderr", DeniedOutput()))
        for control in (
            lambda: __import__("config"), lambda: __import__("stock_tracker.providers.factory"),
            lambda: __import__("stock_tracker.persistence.sqlite_watchlists"),
            lambda: os.environ.get("FMP_API_KEY"), lambda: os.getenv("STOCK_TRACKER_API_TOKEN"),
            lambda: open("startup-probe", "r"), lambda: io.open("startup-probe", "w"),
            lambda: os.open("startup-probe", os.O_RDONLY), lambda: sqlite3.connect(":memory:"),
            lambda: socket.getaddrinfo("example.invalid", 443),
            lambda: socket.socket().connect(("127.0.0.1", 1)),
            lambda: urllib.request.urlopen("https://example.invalid/"),
            lambda: pickle.loads(b"opaque synthetic"), lambda: sys.stdout.write("probe"),
        ):
            try:
                control()
            except (AssertionError, ModuleNotFoundError):
                pass
            else:
                raise AssertionError("A launch configuration denial control failed")
        return load_api_configuration(enable_dashboard=dashboard, enable_upcoming_eps=upcoming_eps, **{name: str(Path.cwd() / name) for name in
            ("database", "history_cache", "menu_legacy", "evaluation_legacy")})


async def help_exercise(create_app):
    # Guarded foundation entry controls deny ordinary data IO, SQL, environment,
    # providers/configuration, CLI/UI, networking, pickle and ordinary output.
    # Only the explicitly requested help may write into this in-memory capture.
    from stock_tracker.api import configuration, composition, launcher
    for module in (configuration, composition, launcher):
        assert Path(module.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
    output = io.StringIO()
    with redirect_stdout(output):
        try:
            launcher.main(["--help"])
        except SystemExit as error:
            assert error.code == 0
        else:
            raise AssertionError("Help did not exit")
    help_text = output.getvalue()
    assert all(option in help_text for option in ("--database", "--history-cache", "--menu-legacy", "--evaluation-legacy", "--enable-history", "--enable-upcoming-eps", "--dashboard"))
    assert "127.0.0.1:8000" in help_text


async def composition_exercise(create_app):
    from stock_tracker.api import composition
    config = _configuration
    with patch.object(composition, "monotonic", lambda: 0.0):
        instance = composition.create_local_app(config)
    diagnostics = []
    class Capture(logging.Handler):
        def emit(self, record):
            diagnostics.append(record.getMessage())
    logger = logging.getLogger("stock_tracker.api.errors")
    logger.addHandler(Capture())
    logger.propagate = False
    for path, headers in (("/health", [(b"host", b"127.0.0.1:8000")]),
                          ("/api/v1/openapi.json", [(b"host", b"127.0.0.1:8000"), (b"authorization", b"Bearer " + config.token.encode())]),
                          ("/api/v1/watchlists/menu_watchlist/entries/0/history", [(b"host", b"127.0.0.1:8000"), (b"authorization", b"Bearer " + config.token.encode())])):
        sent = []
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        async def send(message):
            sent.append(message)
        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET",
                 "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"", "headers": headers,
                 "root_path": "", "client": ("127.0.0.1", 1), "server": ("127.0.0.1", 8000)}
        await instance(scope, receive, send)
        status = sent[0]["status"]
        payload = json.loads(b"".join(message.get("body", b"") for message in sent))
        assert status == (503 if path.endswith("history") else 200)
        if path.endswith("history"):
            assert payload["error"]["code"] == "history_disabled"
    assert diagnostics == ["API operation failed: history_disabled"]
    scope.update(path="/api/v1/research/upcoming-eps", raw_path=b"/api/v1/research/upcoming-eps",
                 query_string=b"provider_symbol=TEST&start=2026-10-18&end=2026-10-31")
    sent = []
    from datetime import datetime, timezone
    class Clock:
        @classmethod
        def now(cls, zone):
            assert zone is timezone.utc
            return datetime(2026, 10, 17, tzinfo=timezone.utc)
    with patch.object(composition, "datetime", Clock):
        await instance(scope, receive, send)
    assert sent[0]["status"] == (429 if config.enable_upcoming_eps else 503)
    expected = "eps_rate_limited" if config.enable_upcoming_eps else "eps_disabled"
    payload = json.loads(b"".join(message.get("body", b"") for message in sent))
    assert payload["error"]["code"] == expected


if __name__ == "__main__":
    # Cold import/help runs before any API module or launch token lookup.
    main(sys.argv[1], help_exercise)
    # Launch permits metadata validation/process token lookup before serving.
    # Prove the smaller launch exception itself: no real process credentials,
    # content IO or infrastructure are available during metadata validation.
    _configuration = guarded_launch_configuration()
    main(sys.argv[1], composition_exercise)
    _configuration = guarded_launch_configuration(dashboard=True)
    main(sys.argv[1], composition_exercise)
    _configuration = guarded_launch_configuration(upcoming_eps=True)
    main(sys.argv[1], composition_exercise)
