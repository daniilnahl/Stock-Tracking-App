"""Saved watchlist HTTP integration using shared services and isolated SQLite."""

import asyncio
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import pickle
import sqlite3
import threading

import pytest

from stock_tracker.api import ApiServices, create_app
from stock_tracker.domain import Stock
from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord
from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
from stock_tracker.services.watchlists import WatchlistService
from test_api_foundation import authorized_headers, credential, invoke, scope


_loop = None


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
        _loop = None


def row(quantity="10", cost="100", price="120", exchange="NASDAQ"):
    return WatchlistEntry(Stock("AAPL", name="Fictional", exchange=exchange), Decimal(quantity),
                         None if cost is None else Decimal(cost), None if price is None else Decimal(price),
                         "Tech", "US", "opaque USD", "N/A", "", "literal [x]", None, "0", "-", "N/A", "2.50", "old")


def app_for(repository, legacy=lambda: False):
    return create_app(token=credential(), services=ApiServices(watchlist=lambda namespace:
                      WatchlistService(repository, namespace=namespace, legacy_present=legacy)))


def request(app, namespace="menu_watchlist", **kwargs):
    return _loop.run_until_complete(invoke(app, scope("/api/v1/watchlists/" + namespace,
                                                     headers=authorized_headers()), **kwargs))


@pytest.mark.parametrize("namespace", ["menu_watchlist", "daniils_stock_method"])
def test_sqlite_saved_exact_values_order_duplicates_and_unknown_provenance(tmp_path, namespace):
    database = tmp_path / "state.sqlite3"
    repository = SQLiteWatchlistRepository(database)
    precise = row("0.12345678901234567890123456789", "100.0000000001", None, None)
    rows = (row(), row(exchange="NYSE"), row("0", None, "0"), row("0", "0", "120"),
            row("10", "0", "120"), row("0.25", "100", "80"), row("0", "100", None), precise)
    repository.save(WatchlistRecord(namespace, "Saved", rows))
    other = "daniils_stock_method" if namespace == "menu_watchlist" else "menu_watchlist"
    repository.save(WatchlistRecord(other, "Other", (replace(row(), stock=Stock("OTHER")),)))
    before = database.read_bytes()
    status, payload, headers, _ = request(app_for(SQLiteWatchlistRepository(database), lambda: pytest.fail("Existing namespace checked legacy")), namespace)
    assert status == 200 and headers[b"cache-control"] == b"no-store"
    assert payload["namespace"] == namespace and payload["name"] == "Saved"
    assert payload["observation"] == "saved"
    assert payload["provenance"] == {"source": None, "observed_at": None, "retrieved_at": None, "freshness": "unknown"}
    entries = payload["entries"]
    assert [entry["ordinal"] for entry in entries] == list(range(8))
    assert [entry["stock"]["symbol"] for entry in entries] == ["AAPL"] * 8
    assert [entry["stock"]["exchange"] for entry in entries[:2]] == ["NASDAQ", "NYSE"]
    assert entries[0]["snapshot"] == {"cost_basis": "1000", "market_value": "1200", "unrealized_pnl": "200", "unrealized_return": "0.2"}
    assert entries[0]["metadata"]["currency"] == "opaque USD"
    assert entries[0]["metadata"]["price_5d"] == "literal [x]"
    assert entries[2]["current_price"] == "0" and entries[2]["average_cost"] is None and entries[2]["snapshot"] is None
    assert entries[3]["snapshot"] == {"cost_basis": "0", "market_value": "0", "unrealized_pnl": "0", "unrealized_return": None}
    assert entries[4]["snapshot"] == {"cost_basis": "0", "market_value": "1200", "unrealized_pnl": "1200", "unrealized_return": None}
    assert entries[5]["snapshot"] == {"cost_basis": "25.00", "market_value": "20.00", "unrealized_pnl": "-5.00", "unrealized_return": "-0.2"}
    assert entries[6]["snapshot"] == {"cost_basis": "0", "market_value": None, "unrealized_pnl": None, "unrealized_return": None}
    assert entries[7]["quantity"] == "0.12345678901234567890123456789"
    assert entries[7]["average_cost"] == "100.0000000001" and entries[7]["current_price"] is None
    assert database.read_bytes() == before
    assert set(tmp_path.iterdir()) == {database}


@pytest.mark.parametrize("namespace", ["menu_watchlist", "daniils_stock_method"])
def test_missing_database_empty_without_create_and_legacy_presence_only(tmp_path, monkeypatch, namespace):
    database, legacy = tmp_path / "state.sqlite3", tmp_path / "opaque.pkl"
    def legacy_present():
        try:
            legacy.lstat()
        except FileNotFoundError:
            return False
        return True
    app = app_for(SQLiteWatchlistRepository(database), legacy_present)
    status, payload, _, _ = request(app, namespace)
    assert status == 200 and payload["name"] == "Watchlist" and payload["entries"] == []
    assert not database.exists()
    legacy.write_bytes(b"untrusted synthetic legacy")
    original_open = Path.open
    def guarded(path, *args, **kwargs):
        if path == legacy:
            pytest.fail("Legacy contents opened")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr(pickle, "load", lambda *a, **k: pytest.fail("Legacy deserialized"))
    monkeypatch.setattr(pickle, "loads", lambda *a, **k: pytest.fail("Legacy deserialized"))
    assert request(app, namespace)[0:2] == (409, {"error": {"code": "legacy_state_present", "message": "Legacy state requires an explicit safe transition."}})
    assert not database.exists()
    monkeypatch.setattr(Path, "open", original_open)
    assert legacy.read_bytes() == b"untrusted synthetic legacy"


@pytest.mark.parametrize("kind", ["corrupt", "future", "malformed"])
def test_bad_sqlite_safe_error_preserves_bytes(tmp_path, kind, caplog):
    database = tmp_path / "state.sqlite3"
    repository = SQLiteWatchlistRepository(database)
    if kind == "corrupt":
        database.write_bytes(b"synthetic corrupt database")
    else:
        repository.save(WatchlistRecord("menu_watchlist", "Saved", (row(),)))
        with sqlite3.connect(database) as connection:
            connection.execute("PRAGMA user_version=99" if kind == "future" else "UPDATE watchlist_entries SET quantity='NaN'")
    before = database.read_bytes()
    assert request(app_for(repository))[0:2] == (500, {"error": {"code": "internal_error", "message": "The operation failed."}})
    assert database.read_bytes() == before and str(database) not in caplog.text


@pytest.mark.parametrize("kind", ["unknown", "auth", "host", "origin", "query", "body", "chunked", "method", "target"])
def test_rejection_precedes_service_acquisition(kind):
    calls = []
    app = create_app(token=credential(), services=ApiServices(watchlist=lambda namespace: calls.append(namespace)))
    request_scope = scope("/api/v1/watchlists/unknown" if kind == "unknown" else "/api/v1/watchlists/menu_watchlist", headers=authorized_headers())
    kwargs, expected = {}, 422
    if kind == "unknown":
        expected = 404
    elif kind == "auth":
        request_scope["headers"] = request_scope["headers"][:1]
        expected = 401
    elif kind == "host":
        request_scope["headers"][0] = (b"host", b"evil.invalid:8000")
        expected = 400
    elif kind == "origin":
        request_scope["headers"].append((b"origin", b"null"))
        expected = 403
    elif kind == "query":
        request_scope["query_string"] = b"hidden=private"
    elif kind == "body":
        request_scope["headers"].append((b"content-length", b"1"))
    elif kind == "chunked":
        kwargs["messages"] = [{"type": "http.request", "body": b"private", "more_body": True}]
    elif kind == "method":
        request_scope["method"] = "POST"
        expected = 405
    elif kind == "target":
        request_scope["raw_path"] = b"/" + b"x" * 2048
        expected = 414
    if kind in ("auth", "host", "origin", "query", "body", "target"):
        kwargs["no_receive"] = True
    result = _loop.run_until_complete(invoke(app, request_scope, **kwargs))
    assert result[0] == expected and calls == []


def test_route_capacity_and_oversize_release_without_queue():
    class Repository:
        def get(self, namespace):
            return WatchlistRecord(namespace, "Saved", (row(),))
    async def scenario():
        started, release = threading.Barrier(5), threading.Event()
        calls = []
        def acquire(namespace):
            calls.append(namespace)
            started.wait(timeout=10)
            assert release.wait(timeout=10)
            return WatchlistService(Repository(), namespace=namespace, legacy_present=lambda: False)
        app = create_app(token=credential(), services=ApiServices(watchlist=acquire))
        request_scope = scope("/api/v1/watchlists/menu_watchlist", headers=authorized_headers())
        tasks = [asyncio.create_task(invoke(app, request_scope)) for _ in range(4)]
        await asyncio.to_thread(started.wait, 10)
        try:
            result = await invoke(app, request_scope)
            assert result[0] == 503 and result[1]["error"]["code"] == "api_busy"
            assert len(calls) == 4
        finally:
            release.set()
        assert all(result[0] == 200 for result in await asyncio.gather(*tasks))
        app.state.api_services = ApiServices(watchlist=lambda namespace: WatchlistService(Repository(), namespace=namespace, legacy_present=lambda: False))
        assert (await invoke(app, request_scope))[0] == 200
    _loop.run_until_complete(scenario())
    class Oversize:
        def get(self, namespace):
            return WatchlistRecord(namespace, "Saved", (replace(row(), sector="x" * (4 * 1024 * 1024)),))
    app = app_for(Oversize())
    assert request(app)[0:2] == (503, {"error": {"code": "response_too_large", "message": "Response exceeds the supported size."}})
    app.state.api_services = ApiServices(watchlist=lambda namespace: WatchlistService(Repository(), namespace=namespace, legacy_present=lambda: False))
    assert request(app)[0] == 200


def test_absent_namespace_existing_database_remains_unchanged(tmp_path):
    database = tmp_path / "state.sqlite3"
    repository = SQLiteWatchlistRepository(database)
    repository.save(WatchlistRecord("daniils_stock_method", "Other", (row(),)))
    before = database.read_bytes()
    status, payload, _, _ = request(app_for(repository))
    assert status == 200 and payload["namespace"] == "menu_watchlist" and payload["entries"] == []
    assert database.read_bytes() == before and set(tmp_path.iterdir()) == {database}


@pytest.mark.parametrize("kind", ["swapped", "forged", "missing"])
def test_bad_injection_never_publishes_wrong_namespace_or_malformed_output(kind):
    class Repository:
        def get(self, namespace):
            return WatchlistRecord(namespace, "Other", (row(),))
    service = WatchlistService(Repository(), namespace="daniils_stock_method", legacy_present=lambda: False)
    if kind == "forged":
        service.view = lambda record: object()
    app = create_app(token=credential(), services=ApiServices(watchlist=None if kind == "missing" else lambda namespace: service))
    assert request(app)[0:2] == (500, {"error": {"code": "internal_error", "message": "The operation failed."}})
