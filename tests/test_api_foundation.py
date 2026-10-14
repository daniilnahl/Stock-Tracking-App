"""In-process HTTP and ASGI access/error/bounds contracts; no real listener."""

import asyncio
from contextlib import suppress
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
import socket

import httpx
import pytest
from fastapi import Request

from stock_tracker.api import ApiServices, create_app, run_data_operation
from stock_tracker.api.errors import ApiFailure
from stock_tracker.api.json_response import BoundedJSONResponse, MAX_RESPONSE_BYTES
from stock_tracker import exceptions as failures
from stock_tracker.domain.errors import DomainValidationError


ROOT = Path(__file__).resolve().parents[1]
_event_loop = None


@pytest.fixture(scope="module", autouse=True)
def native_loop():
    """Bootstrap Windows control sockets before per-test transport denial.

    Actual HTTP/ASGI operations execute with the normal network guard active;
    no policy is replaced and no application listener exists.
    """
    global _event_loop
    _event_loop = asyncio.new_event_loop()
    try:
        yield
    finally:
        _event_loop.run_until_complete(_event_loop.shutdown_asyncgens())
        _event_loop.run_until_complete(_event_loop.shutdown_default_executor())
        _event_loop.close()
        _event_loop = None


def run(coroutine):
    return _event_loop.run_until_complete(coroutine)


def credential():
    return "synthetic_" * 4


def scope(path="/health", *, method="GET", headers=None, query=b""):
    return {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "scheme": "http", "method": method, "path": path, "raw_path": path.encode(),
            "root_path": "", "query_string": query, "headers": headers if headers is not None else [(b"host", b"127.0.0.1:8000")],
            "client": ("127.0.0.1", 12345), "server": ("127.0.0.1", 8000)}


async def invoke(app, request_scope=None, *, messages=None, no_receive=False):
    output, reads = [], []
    incoming = list(messages if messages is not None else [{"type": "http.request", "body": b""}])

    async def receive():
        assert not no_receive, "Rejected request must not consume its body"
        reads.append(True)
        assert incoming, "Body inspection must stop at first nonempty chunk"
        return incoming.pop(0)

    async def send(message):
        output.append(message)

    await app(request_scope or scope(), receive, send)
    start = next(item for item in output if item["type"] == "http.response.start")
    body = b"".join(item.get("body", b"") for item in output if item["type"] == "http.response.body")
    return start["status"], json.loads(body), dict(start["headers"]), len(reads)


def request(app, request_scope=None, **kwargs):
    return run(invoke(app, request_scope, **kwargs))


def authorized_headers():
    return [(b"host", b"127.0.0.1:8000"), (b"authorization", b"Bearer " + credential().encode())]


def test_factory_and_health_are_io_free_and_no_data_routes(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("No service should be acquired")
    app = create_app(services=ApiServices(watchlist=denied))
    assert {route.path for route in app.routes} == {"/health", "/api/v1/openapi.json"}
    status, payload, headers, reads = request(app)
    assert (status, payload, reads) == (200, {"status": "ok"}, 1)
    assert headers[b"cache-control"] == b"no-store"
    assert request(app, scope("/api/v1/openapi.json"))[0:2] == (
        401, {"error": {"code": "unauthorized", "message": "Authentication is required."}})


def test_native_loop_bootstrap_keeps_normal_transport_guards_active():
    with pytest.raises(pytest.fail.Exception, match="Network access denied"):
        socket.getaddrinfo("example.invalid", 443)
    with socket.socket() as candidate:
        with pytest.raises(pytest.fail.Exception, match="Network access denied"):
            candidate.connect(("127.0.0.1", 1))


def test_operator_credential_absent_from_normal_application_diagnostics():
    supplied = credential()
    app = create_app(token=supplied)
    assert supplied not in repr(app)
    assert supplied not in repr(app.user_middleware)
    result = request(app, scope("/api/v1/openapi.json", headers=authorized_headers()))
    assert result[0] == 200
    assert supplied not in repr(app.middleware_stack)
    assert supplied not in json.dumps(app.openapi())


def test_in_process_httpx_schema_snapshot_and_static_no_dependency_work():
    def denied(*args, **kwargs):
        raise AssertionError("No dependency acquisition")
    app = create_app(token=credential(), services=ApiServices(watchlist=denied))

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000") as client:
            response = await client.get("/api/v1/openapi.json", headers={"Authorization": "Bearer " + credential()})
            assert response.status_code == 200
            assert response.headers["cache-control"] == "no-store"
            assert response.json() == json.loads((ROOT / "tests/fixtures/api_foundation_openapi.json").read_text())
            for path in ("/docs", "/redoc", "/openapi.json", "/health/", "/api/v1/watchlists/menu_watchlist"):
                response = await client.get(path, headers={"Authorization": "Bearer " + credential()})
                assert response.status_code == 404
                assert response.json()["error"]["code"] == "not_found"
                assert "location" not in response.headers
    run(scenario())


@pytest.mark.parametrize("headers,code,status", [
    ([], "host_invalid", 400),
    ([(b"host", b"localhost")], "host_invalid", 400),
    ([(b"host", b"evil.invalid:8000")], "host_invalid", 400),
    ([(b"host", b"127.0.0.1:8000"), (b"Host", b"127.0.0.1:8000")], "host_invalid", 400),
    ([(b"host", b"localhost:8000"), (b"origin", b"null")], "origin_forbidden", 403),
    ([(b"host", b"localhost:8000"), (b"origin", b"")], "origin_forbidden", 403),
    ([(b"host", b"127.0.0.1:8000")], "unauthorized", 401),
    ([(b"host", b"localhost:8000"), (b"authorization", b"Basic private-input")], "unauthorized", 401),
    (authorized_headers() + [(b"authorization", b"Bearer duplicate")], "unauthorized", 401),
    ([(b"host", b"localhost:8000"), (b"authorization", b"Bearer  " + credential().encode())], "unauthorized", 401),
    ([(b"host", b"localhost:8000"), (b"authorization", b"Bearer " + b"a" * 257)], "unauthorized", 401),
    ([(b"host", b"localhost:8000"), (b"authorization", b"Bearer " + b"\xff" * 32)], "unauthorized", 401),
    ([(b"host", b"localhost:8000"), (b"authorization", b"Bearer " + b"x" * 32)], "unauthorized", 401),
])
def test_host_origin_and_auth_fail_before_receive(headers, code, status, caplog):
    result = request(create_app(token=credential()), scope("/api/v1/openapi.json", headers=headers), no_receive=True)
    assert (result[0], result[1]["error"]["code"], result[3]) == (status, code, 0)
    assert credential() not in caplog.text and "private-input" not in caplog.text
    assert result[2][b"cache-control"] == b"no-store"
    if status == 401:
        assert result[2][b"www-authenticate"] == b"Bearer"


@pytest.mark.parametrize("value", ["", "short", "x" * 257, "a" * 32 + "\n", "a" * 32 + " ", "é" * 32, 1, True])
def test_invalid_factory_token_is_safe(value):
    with pytest.raises(ValueError, match="^API token configuration is invalid.$"):
        create_app(token=value)


def test_case_insensitive_bearer_and_exact_boundary_tokens():
    for supplied in ("x" * 32, "a_-Z9" * 51 + "a"):
        app = create_app(token=supplied)
        headers = [(b"host", b"localhost:8000"), (b"authorization", b"bEaReR " + supplied.encode())]
        assert request(app, scope("/api/v1/openapi.json", headers=headers))[0] == 200


@pytest.mark.parametrize("header", [b"1", b"00001", b"-1", b"+1", b"abc", b"", b"9" * 5000])
def test_declared_body_or_malformed_length_rejected_without_read(header):
    result = request(create_app(), scope(headers=[(b"host", b"localhost:8000"), (b"content-length", header)]), no_receive=True)
    assert (result[0], result[1]["error"]["code"], result[3]) == (422, "invalid_request", 0)


def test_duplicate_length_and_chunked_nonempty_body_are_bounded():
    assert request(create_app(), scope(headers=[(b"host", b"localhost:8000"),
                                                (b"content-length", b"0"), (b"content-length", b"0")]), no_receive=True)[0] == 422
    result = request(create_app(), messages=[{"type": "http.request", "body": b"", "more_body": True},
                                            {"type": "http.request", "body": b"synthetic private payload", "more_body": True}])
    assert result[0] == 422 and result[3] == 2
    assert "synthetic private payload" not in json.dumps(result[1])


@pytest.mark.parametrize("path", ["/health", "/api/v1/openapi.json"])
def test_fixed_routes_reject_queries_before_receive(path):
    assert request(create_app(token=credential()), scope(path, headers=authorized_headers(), query=b"hidden=private-input"), no_receive=True)[0] == 422


def test_request_target_exact_bound_and_oversize_priority():
    app = create_app()
    assert request(app, scope("/" + "x" * 2047))[0] == 404
    result = request(app, scope("/" + "x" * 2048, headers=[]), no_receive=True)
    assert result[0:2] == (414, {"error": {"code": "request_too_large", "message": "Request target exceeds the supported size."}})


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def test_unsupported_methods_safe_405_and_no_redirect(method):
    result = request(create_app(), scope(method=method))
    assert result[0] == 405 and result[1]["error"]["code"] == "method_not_allowed"
    assert result[2][b"allow"] == b"GET"


@pytest.mark.parametrize("error,code,status", [
    (failures.LegacyStatePresentError(), "legacy_state_present", 409),
    (DomainValidationError("private value"), "invalid_request", 422),
    (failures.HistoryRangeError(), "invalid_request", 422),
    (failures.InvalidTickerError(), "invalid_ticker", 422),
    (failures.MarketDataUnavailableError(), "market_data_unavailable", 503),
    (failures.InstrumentLookupInconclusiveError(), "market_data_unavailable", 503),
    (failures.ProviderTimeoutError(), "provider_timeout", 504),
    (failures.ProviderUnavailableError(), "provider_unavailable", 503),
    (failures.RateLimitError(retry_after_seconds=123.0), "provider_rate_limited", 429),
    (failures.ProviderResponseError(field="symbol"), "provider_response_invalid", 502),
    (failures.ProviderAuthenticationError(), "provider_unavailable", 503),
    (failures.ProviderAccessError(), "provider_unavailable", 503),
    (failures.ProviderRequestError(), "provider_unavailable", 503),
    (failures.PersistenceValidationError(), "internal_error", 500),
    (failures.PersistenceDataError(), "internal_error", 500),
    (failures.SchemaVersionError(), "internal_error", 500),
    (failures.HistoryCacheError(), "internal_error", 500),
    (RuntimeError("private value"), "internal_error", 500),
    (ApiFailure("provider_unavailable"), "provider_unavailable", 503),
])
def test_expected_and_unexpected_failures_use_fixed_envelopes(error, code, status, caplog):
    app = create_app()

    @app.get("/synthetic-test")
    async def fail():
        raise error

    result = request(app, scope("/synthetic-test"))
    assert result[0] == status and result[1]["error"]["code"] == code
    assert b"retry-after" not in result[2]
    assert "private value" not in json.dumps(result[1]) + caplog.text
    assert "Traceback" not in caplog.text


def test_bounded_json_exact_limit_unicode_and_refuses_before_tail():
    assert json.loads(BoundedJSONResponse({"escaped": "x\n\"\\é😀"}).body) == {"escaped": "x\n\"\\é😀"}
    assert len(BoundedJSONResponse("x" * (MAX_RESPONSE_BYTES - 2)).body) == MAX_RESPONSE_BYTES
    with pytest.raises(ApiFailure) as failure:
        BoundedJSONResponse(["x" * MAX_RESPONSE_BYTES, object()])
    assert failure.value.code == "response_too_large"  # unsupported tail was never encoded
    with pytest.raises(TypeError):
        BoundedJSONResponse(0.1)


def test_oversized_success_becomes_fixed_failure():
    app = create_app()

    @app.get("/synthetic-test")
    async def big():
        return BoundedJSONResponse("x" * MAX_RESPONSE_BYTES)

    result = request(app, scope("/synthetic-test"))
    assert result[0] == 503 and result[1]["error"]["code"] == "response_too_large"


def test_four_operation_limit_release_after_success_and_failure():
    async def scenario():
        app, started, release = create_app(), threading.Barrier(5), threading.Event()
        def work():
            started.wait(timeout=5)
            assert release.wait(timeout=5)
            return {"ok": True}
        operations = [asyncio.create_task(run_data_operation(app, work)) for _ in range(4)]
        await asyncio.to_thread(started.wait, 5)
        try:
            with pytest.raises(ApiFailure) as failure:
                await run_data_operation(app, lambda: {"should_not_execute": True})
            assert failure.value.code == "api_busy"
        finally:
            release.set()
        assert all(response.status_code == 200 for response in await asyncio.gather(*operations))
        def fail():
            raise RuntimeError("synthetic failure")
        with pytest.raises(RuntimeError):
            await run_data_operation(app, fail, history=True)
        assert (await run_data_operation(app, lambda: {}, history=True)).status_code == 200
    run(scenario())


def test_actual_asgi_disconnect_holds_history_slot_until_worker_ends():
    async def scenario():
        app = create_app(token=credential())
        started, release = threading.Event(), threading.Event()
        disconnected, completed = asyncio.Event(), threading.Event()
        messages = asyncio.Queue()
        await messages.put({"type": "http.request", "body": b""})

        def provider():
            started.set()
            assert release.wait(timeout=5)
            completed.set()
            return {"synthetic": "data"}

        @app.get("/api/v1/synthetic-test")
        async def synthetic(request: Request):
            operation = asyncio.create_task(run_data_operation(app, provider, history=True))
            while True:
                message = await request.receive()
                if message["type"] == "http.disconnect":
                    disconnected.set()
                    operation.cancel()
                    with suppress(asyncio.CancelledError):
                        await operation
                    return BoundedJSONResponse({"disconnected": True})

        async def send(message):
            pass  # simulate a closed client; delivery no longer reaches it

        handler = asyncio.create_task(app(scope("/api/v1/synthetic-test", headers=authorized_headers()), messages.get, send))
        assert await asyncio.to_thread(started.wait, 5)
        await messages.put({"type": "http.disconnect"})
        await asyncio.wait_for(disconnected.wait(), 5)
        await handler
        try:
            with pytest.raises(ApiFailure) as failure:
                await run_data_operation(app, lambda: {}, history=True)
            assert failure.value.code == "api_busy"
        finally:
            release.set()
        assert await asyncio.to_thread(completed.wait, 5)
        # Await the shielded worker itself, avoiding a wall-clock sleep/race
        # between its completion event and its admission-release finally.
        workers = asyncio.all_tasks() - {asyncio.current_task()}
        await asyncio.gather(*workers)
        assert (await run_data_operation(app, lambda: {}, history=True)).status_code == 200
    run(scenario())


def test_canceled_queued_worker_releases_exactly_once(monkeypatch):
    async def scenario():
        app, gate, started = create_app(), threading.Event(), threading.Event()
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_running_loop()
        original_run = loop.run_in_executor
        submitted = asyncio.Event()

        def occupied():
            started.set()
            assert gate.wait(timeout=5)

        blocker = executor.submit(occupied)
        assert started.wait(timeout=5)

        def queued(ignored_executor, callback, *args):
            result = original_run(executor, callback, *args)
            submitted.set()
            return result

        monkeypatch.setattr(loop, "run_in_executor", queued)
        calls = []
        operation = asyncio.create_task(run_data_operation(app, lambda: calls.append(True), history=True))
        await asyncio.wait_for(submitted.wait(), 5)
        executor.shutdown(wait=False, cancel_futures=True)
        try:
            with pytest.raises(asyncio.CancelledError):
                await operation
            assert calls == []
            app.state.api_admission.reserve(True)
            app.state.api_admission.release(True)
        finally:
            gate.set()
            blocker.result(timeout=5)
            executor.shutdown(wait=True)
    run(scenario())
