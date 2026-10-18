"""Actual source/wheel launcher graph with synthetic native HTTPS and clocks."""

import asyncio
from datetime import datetime, timezone
from contextlib import ExitStack
import io
import json
import logging
import os
from pathlib import Path
import socket
import ssl
import sys
from types import SimpleNamespace
import urllib.request
from unittest.mock import patch


SYNTHETIC_CREDENTIAL = "synthetic-composition-probe-key"


def denied(*args, **kwargs):
    raise AssertionError("EPS composition probe denied external work")


def main(root):
    sys.path.insert(0, str(root))
    if root.name == "src":
        # Source packages and legacy top-level modules have separate roots;
        # installed wheels place both under the one explicit target directory.
        sys.path.insert(1, str(root.parent))
    from stock_tracker.api import launcher, composition
    from stock_tracker.api import errors
    import stock_tracker.providers.finnhub_transport as native
    import stock_tracker.providers.finnhub_factory as factory
    import config
    import uvicorn
    for module in (launcher, composition, native, factory):
        assert Path(module.__file__).resolve().is_relative_to(root)
    # Bootstrap native Windows event-loop control sockets before network denial.
    loop = asyncio.new_event_loop()
    tls_context = ssl.create_default_context()
    synthetic_bearer = "synthetic_" * 4
    now, launches, calls, keys, reads = [0.0], [], [], [], []
    result_status = [200]
    original_load = config.load_finnhub_configuration
    def load():
        keys.append(True)
        return original_load()
    class Clock:
        @classmethod
        def now(cls, zone):
            assert zone is timezone.utc
            return datetime(2026, 10, 17, 20, tzinfo=timezone.utc)
    class Body(io.BytesIO):
        def read(self, size=-1):
            reads.append(size)
            return super().read(size)
    def opened(request, *, timeout):
        assert timeout == 5.0 and request.get_header("X-finnhub-token") == SYNTHETIC_CREDENTIAL
        assert SYNTHETIC_CREDENTIAL not in request.full_url
        calls.append(request.full_url)
        body = Body(b'{"earningsCalendar":[{"symbol":"TEST","date":"2026-10-20","year":2026,"quarter":3,"epsActual":null,"epsEstimate":1.250000000000000001}]}')
        body.status, body.headers = result_status[0], {}
        return body
    async def invoke(app, path="/api/v1/research/upcoming-eps", query=b"provider_symbol=TEST&start=2026-10-18&end=2026-10-31"):
        sent = []
        async def receive():
            return {"type": "http.request", "body": b""}
        async def send(message):
            sent.append(message)
        await app({"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "scheme": "http",
            "method": "GET", "path": path, "raw_path": path.encode(), "query_string": query, "root_path": "",
            "headers": [(b"host", b"127.0.0.1:8000"), (b"authorization", b"Bearer " + synthetic_bearer.encode())],
            "client": ("127.0.0.1", 1), "server": ("127.0.0.1", 8000)}, receive, send)
        return sent[0]["status"], json.loads(b"".join(message.get("body", b"") for message in sent))
    arguments = [value for name in ("database", "history_cache", "menu_legacy", "evaluation_legacy")
                 for value in ("--" + name.replace("_", "-"), str(Path.cwd() / ("eps-probe-" + name)))]
    with ExitStack() as guards:
        guards.enter_context(patch.dict(os.environ, {"STOCK_TRACKER_API_TOKEN": synthetic_bearer,
                                                    "FINNHUB_API_KEY": SYNTHETIC_CREDENTIAL}, clear=True))
        guards.enter_context(patch.object(composition, "monotonic", lambda: now[0]))
        guards.enter_context(patch.object(composition, "datetime", Clock))
        guards.enter_context(patch.object(config, "load_finnhub_configuration", load))
        guards.enter_context(patch.object(config.dotenv, "load_dotenv", denied))
        guards.enter_context(patch.object(native, "build_opener", lambda *args: SimpleNamespace(open=opened)))
        # Bootstrap the native trust context before replacing the entire process
        # environment. Windows crypto initialization needs platform variables;
        # transport URL/header/read logic still executes with networking denied.
        guards.enter_context(patch.object(native.ssl, "create_default_context", lambda **kwargs: tls_context))
        guards.enter_context(patch.object(uvicorn, "run", lambda app, **kwargs: launches.append(app)))
        handler = logging.NullHandler()
        guards.enter_context(patch.object(errors.logger, "handlers", [handler]))
        guards.enter_context(patch.object(errors.logger, "propagate", False))
        for target, attribute in ((socket, "getaddrinfo"), (socket, "create_connection"),
                                  (socket.socket, "connect"), (socket.socket, "connect_ex"),
                                  (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open")):
            guards.enter_context(patch.object(target, attribute, denied))
        try:
            socket.getaddrinfo("example.invalid", 443)
        except AssertionError:
            pass
        else:
            raise AssertionError("Network guard did not run")
        assert launcher.main(arguments) == 0
        default = launches.pop()
        assert loop.run_until_complete(invoke(default))[1]["error"]["code"] == "eps_disabled"
        assert keys == calls == []
        assert launcher.main([*arguments, "--enable-upcoming-eps"]) == 0
        app = launches.pop()
        assert keys == calls == []
        for path in ("/health", "/api/v1/openapi.json"):
            assert loop.run_until_complete(invoke(app, path, b""))[0] == 200
        assert loop.run_until_complete(invoke(app))[1]["error"]["code"] == "eps_rate_limited"
        assert keys == calls == []
        now[0] = 60.0
        status, payload = loop.run_until_complete(invoke(app))
        assert status == 200 and payload["analysis_date"] == "2026-10-17", (status, payload.get("error"), len(calls), len(keys))
        assert payload["observations"][0]["estimate"] == "1.250000000000000001"
        now[0], result_status[0] = 65.0, 429
        assert loop.run_until_complete(invoke(app))[1]["error"]["code"] == "provider_rate_limited"
        now[0] = 124.999999
        assert loop.run_until_complete(invoke(app))[1]["error"]["code"] == "eps_rate_limited"
        assert len(calls) == len(keys) == 2
        now[0], result_status[0] = 125.0, 200
        assert loop.run_until_complete(invoke(app))[0] == 200
        assert len(calls) == len(keys) == 3 and reads == [262145, 262145]
        assert not any(Path(value).exists() for value in arguments[1::2])
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
    loop.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
