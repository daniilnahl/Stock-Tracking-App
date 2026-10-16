"""Installed-wheel static serving, exact allowlist and same-origin boundaries."""

import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
from unittest.mock import patch


def denied(*args, **kwargs):
    raise AssertionError("Application network acquisition")


async def exercise(root):
    from stock_tracker.api import create_app
    from stock_tracker.api import dashboard
    from stock_tracker.api.access import DASHBOARD_HEADERS
    diagnostics = []
    class Capture(logging.Handler):
        def emit(self, record):
            diagnostics.append(record.getMessage())
    logger = logging.getLogger("stock_tracker.api.errors")
    logger.addHandler(Capture())
    logger.propagate = False
    assert Path(dashboard.__file__).resolve().is_relative_to(root)
    resources = {
        "/": ("index.html", "text/html"),
        "/dashboard-assets/hosting.css": ("hosting.css", "text/css"),
        "/dashboard-assets/hosting.js": ("hosting.js", "text/javascript"),
        "/dashboard-assets/stock-pixel.ttf": ("stock-pixel.ttf", "font/ttf"),
        "/dashboard-assets/LICENSE.txt": ("LICENSE.txt", "text/plain"),
    }
    assert dashboard.ASSETS == resources
    directory = root / "stock_tracker/api/dashboard_assets"
    assert {file.name for file in directory.iterdir()} == {name for name, _ in resources.values()}
    expected = {name: (directory / name).read_bytes() for name, _ in resources.values()}
    assert b'<div id="root"></div>' in expected["index.html"]
    assert b'/dashboard-assets/hosting.js' in expected["index.html"]
    assert b'/api/v1/watchlists/' in expected["hosting.js"]
    for name in (b"react 19.3.1 / MIT", b"react-dom 19.3.1 / MIT", b"scheduler 0.28.0 / MIT", b"vite 8.3.4 / MIT"):
        assert name in expected["LICENSE.txt"]
    app = create_app(dashboard=True)
    reads = []
    def allowed_asset(name):
        assert name in expected
        reads.append(name)
        return expected[name]
    async def request(path, *, raw=None, origins=(), host=b"127.0.0.1:8000", query=b"", body=b"", method="GET", instance=app):
        sent = []
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        async def send(message):
            sent.append(message)
        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "scheme": "http",
                 "method": method, "path": path, "raw_path": raw or path.encode(), "root_path": "", "query_string": query,
                 "headers": [(b"host", host), *[(b"origin", value) for value in origins]],
                 "client": ("127.0.0.1", 1), "server": ("127.0.0.1", 8000)}
        await instance(scope, receive, send)
        return sent[0]["status"], dict(sent[0]["headers"]), b"".join(m.get("body", b"") for m in sent)
    # Actual wheel files are served, not fixtures, before guarded refusals.
    for route, (name, media_type) in resources.items():
        status, headers, body = await request(route, origins=(b"http://127.0.0.1:8000",))
        assert status == 200 and body == expected[name]
        assert headers[b"content-type"].decode().split(";")[0] == media_type
        assert all(headers[key] == value for key, value in DASHBOARD_HEADERS)
    with patch.object(dashboard, "resource_bytes", allowed_asset):
        assert (await request("/", origins=(b"http://localhost:8000",), host=b"localhost:8000"))[0] == 200
        reads.clear()
        assert (await request("/api/v1/openapi.json"))[0] == 401
        assert (await request("/", origins=(b"null",)))[0] == 403
        assert (await request("/", origins=(b"http://localhost:8000",)))[0] == 403
        assert (await request("/", origins=(b"http://127.0.0.1:8000",) * 2))[0] == 403
        assert (await request("/", host=b"outside.invalid"))[0] == 400
        assert (await request("/", query=b"hidden=1"))[0] == 422
        assert (await request("/", body=b"hidden"))[0] == 422
        assert (await request("/", method="POST"))[0] == 405
        assert (await request("/dashboard-assets/hosting.js", raw=b"/dashboard-assets/%68osting.js"))[0] == 404
        assert (await request("/dashboard-assets/../configuration.py"))[0] == 404
        assert (await request("/", instance=create_app()))[0] == 404
        status, _, body = await request("/health")
        assert status == 200 and json.loads(body) == {"status": "ok"}
        assert reads == []
    assert diagnostics == ["API operation failed: " + code for code in (
        "unauthorized", "origin_forbidden", "origin_forbidden", "origin_forbidden",
        "host_invalid", "invalid_request", "invalid_request", "not_found")]


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root))
    loop = asyncio.new_event_loop()
    try:
        with patch.object(socket, "getaddrinfo", denied), patch.object(socket.socket, "connect", denied):
            loop.run_until_complete(exercise(root))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
        loop.close()
