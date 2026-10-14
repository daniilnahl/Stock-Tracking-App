"""Stored-row history transport over actual services and isolated state."""

import asyncio
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pickle
import threading
from types import SimpleNamespace

import pytest

from stock_tracker.api import ApiServices, create_app
from stock_tracker.domain import Stock
from stock_tracker.persistence.models import WatchlistRecord
from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
from stock_tracker.providers.models import PriceBar
from stock_tracker.services import HistoryService, WatchlistService
from stock_tracker.services.models import HistoryView
from test_api_foundation import authorized_headers, credential, invoke, scope
from test_api_watchlists import row


NOW = datetime(2020, 3, 1, tzinfo=timezone.utc)
START, END = date(2020, 1, 2), date(2020, 1, 6)
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


def bar(session=START, volume=0):
    return PriceBar("AAPL", session, Decimal("100.00"), Decimal("120"), Decimal("99"),
                    Decimal("110.0000000000000000001"), None, volume)


def app_for(repository, history, *, enabled=True, legacy=lambda: False, **kwargs):
    return create_app(token=credential(), services=ApiServices(
        watchlist=lambda namespace: WatchlistService(repository, namespace=namespace, legacy_present=legacy),
        history=history, history_enabled=enabled, **kwargs))


def request(app, ordinal="0", namespace="menu_watchlist", query=b"start=2020-01-02&end=2020-01-06", **kwargs):
    return _loop.run_until_complete(invoke(app, scope(
        f"/api/v1/watchlists/{namespace}/entries/{ordinal}/history", headers=authorized_headers(), query=query), **kwargs))


@pytest.mark.parametrize("namespace", ["menu_watchlist", "daniils_stock_method"])
def test_exact_loaded_duplicate_rows_sparse_decimal_and_preserved_state(tmp_path, namespace):
    database, legacy = tmp_path / "state.sqlite3", tmp_path / "legacy.pkl"
    legacy.write_bytes(b"opaque synthetic legacy")
    repository = SQLiteWatchlistRepository(database)
    rows = (row(exchange="NYSE"), replace(row(), stock=Stock("AAPL", name="First", exchange="NASDAQ")),
            replace(row(), stock=Stock("AAPL", name="Second", exchange="NASDAQ")))
    repository.save(WatchlistRecord(namespace, "Saved", rows))
    calls = []
    def source(ordinal):
        calls.append(ordinal)
        return SimpleNamespace(get_price_history=lambda symbol, start, end: [bar(), bar(END, 9223372036854775807)])
    history = HistoryService(source, clock=lambda: NOW)
    app = app_for(repository, history, legacy=lambda: pytest.fail("Existing namespace checked legacy"))
    before = database.read_bytes(), legacy.read_bytes()
    status, payload, headers, _ = request(app, "2", namespace)
    assert status == 200 and payload["ordinal"] == 2 and payload["stock"]["name"] == "Second"
    assert calls == [2] and headers[b"cache-control"] == b"no-store"
    assert payload["start"] == START.isoformat() and payload["end"] == END.isoformat()
    assert payload["price_basis"] == "raw"
    assert payload["provenance"] == {"source": None, "observed_at": None, "retrieved_at": None, "currency": None, "freshness": "unknown"}
    assert payload["bars"] == [{"symbol": "AAPL", "date": session.isoformat(), "open": "100.00", "high": "120",
                                "low": "99", "close": "110.0000000000000000001", "adjusted_close": None, "volume": volume}
                               for session, volume in [(START, 0), (END, 9223372036854775807)]]
    assert request(app, "0", namespace)[0] == 503 and calls == [2]
    assert request(app, "1", namespace)[1]["stock"]["name"] == "First" and calls == [2, 1]
    assert request(app, "3", namespace)[0] == 404
    assert (database.read_bytes(), legacy.read_bytes()) == before
    assert set(tmp_path.iterdir()) == {database, legacy}


@pytest.mark.parametrize("ordinal", ["-1", "+1", "1.0", "1e0", "True", "１", " 0"])
def test_invalid_ordinal_before_acquisition(ordinal):
    app = create_app(token=credential(), services=ApiServices(watchlist=lambda namespace: pytest.fail("Acquired"), history_enabled=True))
    assert request(app, ordinal)[0] == 422


@pytest.mark.parametrize("query", [b"start=2020-01-02", b"end=2020-01-06", b"start=&end=2020-01-06",
    b"start=2020-1-02&end=2020-01-06", b"start=2020-02-30&end=2020-03-01", b"start=0000-01-01&end=2020-01-06",
    b"start=2020-01-02&end=2020-01-06&x=1", b"start=2020-01-02&start=2020-01-02",
    b"start=2020-01-02&end=2020-01-06&end=2020-01-06", b"x", b"start=%FF&end=2020-01-06"])
def test_bad_date_grammar_before_acquisition(query):
    app = create_app(token=credential(), services=ApiServices(watchlist=lambda namespace: pytest.fail("Acquired"), history_enabled=True))
    assert request(app, query=query)[0] == 422


def test_disabled_default_before_state_history_cache_and_unknown_namespace():
    app = create_app(token=credential(), services=ApiServices(watchlist=lambda namespace: pytest.fail("Acquired")))
    assert request(app)[0:2] == (503, {"error": {"code": "history_disabled", "message": "Historical acquisition is disabled."}})
    assert request(app, namespace="unknown")[0] == 404


def test_defaults_leap_day_and_calendar_range_policy(tmp_path):
    repository = SQLiteWatchlistRepository(tmp_path / "state.sqlite3")
    repository.save(WatchlistRecord("menu_watchlist", "Saved", (row(),)))
    calls, clocks = [], []
    def clock():
        clocks.append(1)
        return NOW
    def source(ordinal):
        def get(symbol, start, end):
            calls.append((ordinal, symbol, start, end))
            return [bar(date(2020, 2, 29))]
        return SimpleNamespace(get_price_history=get)
    app = app_for(repository, HistoryService(source, clock=clock))
    status, payload, _, _ = request(app, query=b"")
    assert status == 200 and (payload["start"], payload["end"]) == ("2015-02-28", "2020-02-29")
    assert clocks == [1] and calls == [(0, "AAPL", date(2015, 2, 28), date(2020, 2, 29))]
    for query in (b"start=2020-01-06&end=2020-01-02", b"start=2020-01-02&end=2020-03-01",
                  b"start=2000-01-01&end=2020-01-06"):
        assert request(app, query=query)[0] == 422
    assert len(calls) == 1


@pytest.mark.parametrize("kind", ["swapped_namespace", "swapped_stock", "forged", "wrong_range", "missing"])
def test_malformed_or_swapped_injections_fail_safely(kind):
    class Repository:
        def get(self, namespace):
            return WatchlistRecord(namespace, "Saved", (row(),))
    service = WatchlistService(Repository(), namespace="menu_watchlist", legacy_present=lambda: False)
    def history(stock, **kwargs):
        if kind == "forged":
            return object()
        return HistoryView(Stock("AAPL", name="Swapped", exchange="NYSE") if kind == "swapped_stock" else stock,
                           END if kind == "wrong_range" else START, END, (bar(),))
    if kind == "swapped_namespace":
        service.load = lambda: WatchlistRecord("daniils_stock_method", "Other", (row(),))
    app = create_app(token=credential(), services=ApiServices(watchlist=lambda namespace: service,
                     history=None if kind == "missing" else SimpleNamespace(history=history), history_enabled=True))
    assert request(app)[0:2] == (500, {"error": {"code": "internal_error", "message": "The operation failed."}})


@pytest.mark.parametrize("name,status,code", [
    ("ProviderTimeoutError", 504, "provider_timeout"), ("RateLimitError", 429, "provider_rate_limited"),
    ("ProviderResponseError", 502, "provider_response_invalid"), ("ProviderUnavailableError", 503, "provider_unavailable"),
    ("MarketDataUnavailableError", 503, "market_data_unavailable"), ("HistoryCacheError", 500, "internal_error"),
    ("InvalidTickerError", 422, "invalid_ticker"), ("RuntimeError", 500, "internal_error")])
def test_typed_failures_safe_and_preserve_holdings_legacy(tmp_path, monkeypatch, caplog, name, status, code):
    from stock_tracker import exceptions
    database, legacy = tmp_path / "state.sqlite3", tmp_path / "legacy.pkl"
    legacy.write_bytes(b"opaque synthetic legacy")
    repository = SQLiteWatchlistRepository(database)
    repository.save(WatchlistRecord("menu_watchlist", "Saved", (row(),)))
    before = database.read_bytes(), legacy.read_bytes()
    monkeypatch.setattr(pickle, "loads", lambda *args: pytest.fail("Legacy read"))
    def fail(symbol, start, end):
        raise RuntimeError("private path/token") if name == "RuntimeError" else getattr(exceptions, name)()
    app = app_for(repository, HistoryService(lambda ordinal: SimpleNamespace(get_price_history=fail), clock=lambda: NOW))
    result = request(app)
    assert result[0] == status and result[1]["error"]["code"] == code
    assert b"retry-after" not in result[2] and "private" not in caplog.text
    assert (database.read_bytes(), legacy.read_bytes()) == before


@pytest.mark.parametrize("exchange", [None, "NYSE", "nasdaq", "XNAS", "N/A"])
def test_unsupported_selected_exchange_before_history_source(exchange):
    class Repository:
        def get(self, namespace):
            return WatchlistRecord(namespace, "Saved", (row(exchange=exchange),))
    app = app_for(Repository(), HistoryService(lambda ordinal: pytest.fail("History acquired"), clock=lambda: pytest.fail("Clock acquired")))
    result = request(app)
    assert result[0] == 503 and result[1]["error"]["code"] == "market_data_unavailable"


@pytest.mark.parametrize("name", ["ProviderAuthenticationError", "ProviderAccessError", "ProviderRequestError"])
def test_upstream_auth_access_request_are_safe_503(name):
    from stock_tracker import exceptions
    class Repository:
        def get(self, namespace):
            return WatchlistRecord(namespace, "Saved", (row(),))
    def source(ordinal):
        raise getattr(exceptions, name)()
    result = request(app_for(Repository(), HistoryService(source, clock=lambda: NOW)))
    assert result[0] == 503 and result[1]["error"]["code"] == "provider_unavailable"


@pytest.mark.parametrize("kind", ["legacy", "corrupt", "future"])
def test_state_failures_and_legacy_contents_unchanged_before_provider(tmp_path, monkeypatch, kind):
    import sqlite3
    database, legacy = tmp_path / "state.sqlite3", tmp_path / "legacy.pkl"
    legacy.write_bytes(b"opaque synthetic legacy")
    repository = SQLiteWatchlistRepository(database)
    if kind == "corrupt":
        database.write_bytes(b"synthetic corrupt state")
    elif kind == "future":
        repository.save(WatchlistRecord("menu_watchlist", "Saved", (row(),)))
        with sqlite3.connect(database) as connection:
            connection.execute("PRAGMA user_version=99")
    before = database.read_bytes() if database.exists() else None
    original = __import__("pathlib").Path.open
    def opened(path, *args, **kwargs):
        if path == legacy:
            pytest.fail("Legacy contents opened")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(__import__("pathlib").Path, "open", opened)
    history = HistoryService(lambda ordinal: pytest.fail("Provider reached"), clock=lambda: NOW)
    result = request(app_for(repository, history, legacy=lambda: legacy.exists()))
    assert result[0] == (409 if kind == "legacy" else 500)
    assert (database.read_bytes() if database.exists() else None) == before
    monkeypatch.setattr(__import__("pathlib").Path, "open", original)
    assert legacy.read_bytes() == b"opaque synthetic legacy"


@pytest.mark.parametrize("kind", ["nullable", "wrong_symbol", "adjusted", "duplicate", "oversize_volume", "empty"])
def test_history_provider_shape_nulls_and_failures(kind):
    class Repository:
        def get(self, namespace):
            return WatchlistRecord(namespace, "Saved", (row(),))
    bars = {"nullable": [bar(volume=None)], "wrong_symbol": [replace(bar(), symbol="OTHER")],
            "adjusted": [replace(bar(), adjusted_close=Decimal(1))], "duplicate": [bar(), bar()],
            "oversize_volume": [replace(bar(), volume=9223372036854775808)], "empty": []}[kind]
    history = HistoryService(lambda ordinal: SimpleNamespace(get_price_history=lambda *args: bars), clock=lambda: NOW)
    result = request(app_for(Repository(), history))
    if kind == "nullable":
        assert result[0] == 200 and result[1]["bars"][0]["volume"] is None
    else:
        assert result[0] == (503 if kind == "empty" else 502)


@pytest.mark.parametrize("kind", ["auth", "host", "origin", "body", "method", "target", "chunked"])
def test_access_rejections_never_acquire_history_or_state(kind):
    app = create_app(token=credential(), services=ApiServices(watchlist=lambda namespace: pytest.fail("State acquired"), history_enabled=True))
    request_scope = scope("/api/v1/watchlists/menu_watchlist/entries/0/history", headers=authorized_headers())
    kwargs, status = {}, 422
    if kind == "auth":
        request_scope["headers"] = request_scope["headers"][:1]
        status = 401
    elif kind == "host":
        request_scope["headers"][0] = (b"host", b"evil.invalid:8000")
        status = 400
    elif kind == "origin":
        request_scope["headers"].append((b"origin", b"null"))
        status = 403
    elif kind == "body":
        request_scope["headers"].append((b"content-length", b"1"))
    elif kind == "method":
        request_scope["method"] = "POST"
        status = 405
    elif kind == "target":
        request_scope["raw_path"] = b"/" + b"x" * 2048
        status = 414
    else:
        kwargs["messages"] = [{"type": "http.request", "body": b"private", "more_body": True}]
    assert _loop.run_until_complete(invoke(app, request_scope, **kwargs))[0] == status


def test_openapi_parameters_unique_and_exact_integer_limits():
    document = create_app().openapi()
    operation = document["paths"]["/api/v1/watchlists/{namespace}/entries/{ordinal}/history"]["get"]
    parameters = operation["parameters"]
    assert len({(item["name"], item["in"]) for item in parameters}) == len(parameters) == 4
    ordinal = next(item for item in parameters if item["name"] == "ordinal")
    assert ordinal["schema"]["pattern"] == "^[0-9]+$"
    assert {item["name"] for item in parameters if item["in"] == "query"} == {"start", "end"}
    for name in ("start", "end"):
        assert next(item for item in parameters if item["name"] == name)["schema"]["format"] == "date"
    schemas = document["components"]["schemas"]
    assert type(schemas["HistoryResponse"]["properties"]["ordinal"]["minimum"]) is int
    volume = next(item for item in schemas["BarResponse"]["properties"]["volume"]["anyOf"] if item["type"] == "integer")
    assert type(volume["maximum"]) is int and volume["maximum"] == 9223372036854775807


def test_real_cache_restart_exact_expiry_no_stale_fallback(tmp_path):
    from stock_tracker.providers.history_cache import CachedHistoricalMarketDataProvider
    from stock_tracker.persistence.history_cache import JsonHistoryCacheRepository
    from stock_tracker.providers.models import HistoryObservation
    from stock_tracker.providers.transport import ProviderPolicy
    from stock_tracker.exceptions import ProviderUnavailableError
    database, cache, legacy = (tmp_path / name for name in ("state.sqlite3", "history.json", "legacy.pkl"))
    legacy.write_bytes(b"opaque synthetic legacy")
    repository = SQLiteWatchlistRepository(database)
    repository.save(WatchlistRecord("menu_watchlist", "Saved", (row(),)))
    before = database.read_bytes(), legacy.read_bytes()
    now, calls = [NOW], []
    def load(symbol, start, end):
        calls.append((symbol, start, end))
        if len(calls) > 1:
            raise ProviderUnavailableError()
        return HistoryObservation((bar(),), now[0])
    def build():
        provider = CachedHistoricalMarketDataProvider(repository=JsonHistoryCacheRepository(cache, lambda: now[0]),
                    loader=load, clock=lambda: now[0], policy=ProviderPolicy(
                        timeout_seconds=10.0, max_attempts=2, retryable_statuses=frozenset({408, 500, 502, 503, 504}),
                        backoff_base_seconds=0.5, backoff_cap_seconds=2.0, retry_budget_seconds=30.0,
                        retry_on_429=False, quote_cache_ttl_seconds=0.0, history_cache_ttl_seconds=3600.0,
                        stale_cache_fallback=False))
        return app_for(SQLiteWatchlistRepository(database), HistoryService(lambda ordinal: provider, clock=lambda: now[0]),
                       history_source="fmp", history_cache_policy=True)
    first = request(build())
    assert first[0] == 200 and first[1]["provenance"]["freshness"] == "accepted_cache_policy"
    saved = cache.read_bytes()
    now[0] += timedelta(seconds=3599)
    assert request(build())[1] == first[1] and len(calls) == 1
    now[0] += timedelta(seconds=1)
    assert request(build())[0:2] == (503, {"error": {"code": "provider_unavailable", "message": "Market-data provider is unavailable."}})
    assert len(calls) == 2 and cache.read_bytes() == saved
    assert (database.read_bytes(), legacy.read_bytes()) == before


def test_real_history_route_cancellation_retains_admission_until_worker_finishes(monkeypatch):
    class Repository:
        def get(self, namespace):
            return WatchlistRecord(namespace, "Saved", (row(),))
    async def scenario():
        started, release = threading.Event(), threading.Event()
        calls = []
        def get(symbol, start, end):
            calls.append(symbol)
            started.set()
            assert release.wait(timeout=10)
            return [bar()]
        app = app_for(Repository(), HistoryService(lambda ordinal: SimpleNamespace(get_price_history=get), clock=lambda: NOW))
        request_scope = scope("/api/v1/watchlists/menu_watchlist/entries/0/history", headers=authorized_headers(),
                              query=b"start=2020-01-02&end=2020-01-06")
        tasks = []
        original_create = asyncio.create_task
        def create(coroutine, **kwargs):
            task = original_create(coroutine, **kwargs)
            tasks.append(task)
            return task
        monkeypatch.setattr(asyncio, "create_task", create)
        task = asyncio.create_task(invoke(app, request_scope))
        assert await asyncio.to_thread(started.wait, 10)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        try:
            busy = await invoke(app, request_scope)
            assert busy[0] == 503 and busy[1]["error"]["code"] == "api_busy" and calls == ["AAPL"]
        finally:
            release.set()
        await asyncio.gather(*[worker for worker in tasks if worker is not task])
        assert app.state.api_admission._active == app.state.api_admission._history == 0
        assert (await invoke(app, request_scope))[0] == 200
    _loop.run_until_complete(scenario())


def test_real_history_route_closed_asgi_client_keeps_slot_until_provider_terminates():
    class Repository:
        def get(self, namespace):
            return WatchlistRecord(namespace, "Saved", (row(),))
    async def scenario():
        started, release = threading.Event(), threading.Event()
        def get(symbol, start, end):
            started.set()
            assert release.wait(timeout=10)
            return [bar()]
        app = app_for(Repository(), HistoryService(lambda ordinal: SimpleNamespace(get_price_history=get), clock=lambda: NOW))
        request_scope = scope("/api/v1/watchlists/menu_watchlist/entries/0/history", headers=authorized_headers(),
                              query=b"start=2020-01-02&end=2020-01-06")
        incoming = asyncio.Queue()
        await incoming.put({"type": "http.request", "body": b"", "more_body": False})
        closed, sent = False, []
        async def receive():
            return await incoming.get()
        async def send(message):
            if closed:
                raise OSError("Synthetic ASGI client disconnected")
            sent.append(message)
        first = asyncio.create_task(app(request_scope, receive, send))
        assert await asyncio.to_thread(started.wait, 10)
        # The transport queues a real disconnect and refuses further delivery;
        # this nonstreaming adapter need not poll receive while work is running.
        closed = True
        await incoming.put({"type": "http.disconnect"})
        try:
            busy = await invoke(app, request_scope)
            assert busy[0] == 503 and busy[1]["error"]["code"] == "api_busy"
            assert not first.done() and sent == []
        finally:
            release.set()
        await first
        assert sent == [] and app.state.api_admission._active == app.state.api_admission._history == 0
        assert (await invoke(app, request_scope))[0] == 200
    _loop.run_until_complete(scenario())
