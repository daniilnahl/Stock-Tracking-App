"""Offline dashboard boundary and packaged resource checks; no real listener."""

import asyncio
import json
from pathlib import Path
import subprocess

import httpx
import pytest

from stock_tracker.api import create_app
from stock_tracker.api import dashboard
from stock_tracker.api.access import DASHBOARD_HEADERS
from test_api_foundation import credential, scope
from test_api_launcher import configured
from stock_tracker.api.composition import create_local_app


_loop = None


def test_distribution_text_bytes_survive_windows_autocrlf_checkout(tmp_path):
    root = Path(__file__).resolve().parents[1]
    names = ["frontend/index.html", *["src/stock_tracker/api/dashboard_assets/" + name for name in
             ("index.html", "hosting.js", "hosting.css", "LICENSE.txt")]]
    (tmp_path / ".gitattributes").write_bytes((root / ".gitattributes").read_bytes())
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / name).read_bytes())
    def git(*args):
        subprocess.run(["git", "-c", "core.autocrlf=true", *args], cwd=tmp_path,
                       check=True, capture_output=True)
    git("init", "--quiet")
    git("add", ".gitattributes", *names)
    destination = tmp_path / "checkout"
    git("checkout-index", "--all", "--prefix=" + destination.as_posix() + "/")
    for name in names:
        original = (root / name).read_bytes()
        assert b"\r\n" not in original
        assert (destination / name).read_bytes() == original


@pytest.fixture(scope="module", autouse=True)
def native_loop():
    global _loop
    _loop = asyncio.new_event_loop()
    try:
        yield
    finally:
        _loop.run_until_complete(_loop.shutdown_asyncgens())
        _loop.run_until_complete(_loop.shutdown_default_executor())
        _loop.close()


def exchange(app, request_scope=None, *, body=b"", no_receive=False):
    sent = []
    first = True
    async def receive():
        nonlocal first
        assert not no_receive, "Rejected request acquired body"
        if first:
            first = False
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}
    async def send(message):
        sent.append(message)
    _loop.run_until_complete(app(request_scope or scope("/"), receive, send))
    return sent[0]["status"], dict(sent[0]["headers"]), b"".join(m.get("body", b"") for m in sent)


def test_packaged_resources_exact_content_and_headers_without_application_work(tmp_path, monkeypatch):
    config = configured(tmp_path, monkeypatch, enable_dashboard=True)
    app = create_local_app(config)
    # Construction/health/schema do not need any asset data; only static GET does.
    original = dashboard.resource_bytes
    reads = []
    def resource(name):
        reads.append(name)
        return original(name)
    monkeypatch.setattr(dashboard, "resource_bytes", resource)
    assert set(dashboard.ASSETS) == {"/", "/dashboard-assets/hosting.css", "/dashboard-assets/hosting.js",
                                      "/dashboard-assets/stock-pixel.ttf", "/dashboard-assets/LICENSE.txt"}
    for route, (name, media_type) in dashboard.ASSETS.items():
        status, headers, body = exchange(app, scope(route))
        assert status == 200 and body == original(name)
        assert headers[b"content-type"].decode().split(";")[0] == media_type
        assert headers[b"cache-control"] == b"no-store"
        assert all(headers[key] == value for key, value in DASHBOARD_HEADERS)
        assert credential().encode() not in body
    assert reads == [name for name, _ in dashboard.ASSETS.values()]
    assert not list(tmp_path.iterdir())
    html = original("index.html").decode()
    assert 'src="/dashboard-assets/hosting.js"' in html and 'type="module"' in html
    assert '<style' not in html and 'style=' not in html
    assert '<div id="root"></div>' in html and "Hosting readiness demo" not in html
    assert "/api/v1/watchlists/" in original("hosting.js").decode()
    root = Path(__file__).resolve().parents[1]
    assert original("stock-pixel.ttf") == (root / "docs/previews/assets/stock-pixel.ttf").read_bytes()
    license_text = original("LICENSE.txt").decode()
    assert (root / "LICENSE").read_text(encoding="utf-8").strip() in license_text
    for package in ("react 19.3.1", "react-dom 19.3.1", "scheduler 0.28.0", "vite 8.3.4"):
        assert package + " / MIT" in license_text
    assert "Copyright (c) Meta Platforms, Inc. and affiliates." in license_text
    assert "Copyright (c) 2019-present, VoidZero Inc. and Vite contributors" in license_text
    assert "# Licenses of bundled dependencies" not in license_text


@pytest.mark.parametrize("host", [b"localhost:8000", b"127.0.0.1:8000"])
def test_exact_origin_pair_and_auth_remain_required(host):
    app = create_app(token=credential(), dashboard=True)
    headers = [(b"host", host), (b"origin", b"http://" + host)]
    assert exchange(app, scope("/", headers=headers))[0] == 200
    status, _, body = exchange(app, scope("/api/v1/openapi.json", headers=headers), no_receive=True)
    assert status == 401 and json.loads(body)["error"]["code"] == "unauthorized"
    headers.append((b"authorization", b"Bearer " + credential().encode()))
    assert exchange(app, scope("/api/v1/openapi.json", headers=headers))[0] == 200
    assert create_app().openapi() == app.openapi()
    assert exchange(create_app(token=credential()), scope("/", headers=headers), no_receive=True)[0] == 403


@pytest.mark.parametrize("origins", [[b"null"], [b""], [b"https://127.0.0.1:8000"],
    [b"http://localhost:8000"], [b"http://127.0.0.1:8000/"], [b"http://outside.invalid"],
    [b"http://127.0.0.1:8000", b"http://127.0.0.1:8000"]])
def test_disallowed_origins_before_receive_or_asset_io(origins, monkeypatch):
    monkeypatch.setattr(dashboard, "resource_bytes", lambda *a: pytest.fail("Asset IO"))
    headers = [(b"host", b"127.0.0.1:8000"), *[(b"origin", origin) for origin in origins]]
    assert exchange(create_app(dashboard=True), scope("/", headers=headers), no_receive=True)[0] == 403


@pytest.mark.parametrize("path", ["/index.html", "/dashboard-assets/", "/dashboard-assets/index.html",
    "/dashboard-assets/../configuration.py", "/dashboard-assets/..\\configuration.py",
    "/dashboard-assets/hosting.js.map", "/dashboard-assets/.env", "/docs", "/anything"])
def test_no_fallback_or_discovery(path, monkeypatch):
    monkeypatch.setattr(dashboard, "resource_bytes", lambda *a: pytest.fail("Asset IO"))
    assert exchange(create_app(dashboard=True), scope(path))[0] == 404


@pytest.mark.parametrize("raw", [b"/dashboard-assets/%68osting.js", b"/dashboard-assets/x/../hosting.js",
    b"/dashboard-assets/%2e%2e/hosting.js", b"/dashboard-assets%2fhosting.js"])
def test_encoded_and_normalized_aliases_not_accepted(raw, monkeypatch):
    monkeypatch.setattr(dashboard, "resource_bytes", lambda *a: pytest.fail("Asset IO"))
    request = scope("/dashboard-assets/hosting.js")
    request["raw_path"] = raw
    assert exchange(create_app(dashboard=True), request, no_receive=True)[0] == 404


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def test_static_methods_refused(method, monkeypatch):
    monkeypatch.setattr(dashboard, "resource_bytes", lambda *a: pytest.fail("Asset IO"))
    assert exchange(create_app(dashboard=True), scope("/", method=method))[0] == 405


def test_query_body_host_missing_resource_and_default_refusal(monkeypatch, caplog):
    app = create_app(dashboard=True)
    for query in (b"v=1", b"token=synthetic-private"):
        assert exchange(app, scope("/", query=query), no_receive=True)[0] == 422
    assert exchange(app, scope("/"), body=b"synthetic-private")[0] == 422
    headers = [(b"host", b"outside.invalid")]
    assert exchange(app, scope("/", headers=headers), no_receive=True)[0] == 400
    assert exchange(create_app(), scope("/"))[0] == 404
    def missing(name):
        raise FileNotFoundError("synthetic-private-file")
    monkeypatch.setattr(dashboard, "resource_bytes", missing)
    status, headers, body = exchange(app)
    assert status == 500 and json.loads(body)["error"]["code"] == "internal_error"
    assert b"synthetic-private" not in body and "synthetic-private" not in caplog.text
    assert headers[b"content-security-policy"] == dict(DASHBOARD_HEADERS)[b"content-security-policy"]


def test_httpx_real_asgi_rejects_raw_traversal_alias():
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(dashboard=True)),
                                     base_url="http://127.0.0.1:8000") as client:
            for path in ("/dashboard-assets/%2e%2e/configuration.py", "/dashboard-assets/%68osting.js"):
                assert (await client.get(path)).status_code == 404
    _loop.run_until_complete(scenario())
