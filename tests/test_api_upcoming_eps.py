"""Injected EPS HTTP contract with fixed observations and no external IO."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import threading
from types import SimpleNamespace

import pytest

from stock_tracker.api import ApiServices, create_app, run_data_operation
from stock_tracker.api.errors import ApiFailure
from stock_tracker.providers.eps import UpcomingEpsEstimate
from stock_tracker.services import UpcomingEpsService, UpcomingEpsView
from stock_tracker import exceptions as errors
from test_api_foundation import authorized_headers, credential, invoke, scope


PATH = "/api/v1/research/upcoming-eps"
QUERY = b"provider_symbol=TEST&start=2026-10-18&end=2027-01-17"
ANALYSIS, START, END = date(2026, 10, 17), date(2026, 10, 18), date(2027, 1, 17)
STAMP = datetime(2026, 10, 17, 20, tzinfo=timezone.utc)
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


def observation(quarter=3, estimate=Decimal("1.250000000000000001"), **changes):
    return replace(UpcomingEpsEstimate("TEST", 2026, quarter, date(2026, 10, 20), "amc", estimate, STAMP), **changes)


@pytest.fixture
def rig():
    state = SimpleNamespace(calls=[], result=(observation(),), analysis_date=ANALYSIS, error=None)
    def research_date():
        state.calls.append("date")
        return state.analysis_date
    def source():
        state.calls.append("source")
        def get(symbol, **kwargs):
            state.calls.append((symbol, kwargs))
            if state.error is not None:
                raise state.error
            return state.result
        return SimpleNamespace(get_upcoming_eps=get)
    state.service = UpcomingEpsService(source, research_date=research_date)
    state.app = create_app(token=credential(), services=ApiServices(upcoming_eps=state.service, upcoming_eps_enabled=True))
    return state


def request(app, query=QUERY, **kwargs):
    return _loop.run_until_complete(invoke(app, scope(PATH, query=query, headers=authorized_headers()), **kwargs))


def test_precise_context_and_all_explicit_metadata(rig):
    rig.result = tuple(observation(index + 1, value, retrieved_at=STAMP.replace(microsecond=123456))
                       for index, value in enumerate((Decimal("1.250000000000000001"), Decimal("0"), Decimal("-0.25"), None)))
    status, payload, headers, _ = request(rig.app)
    assert status == 200 and headers[b"cache-control"] == b"no-store"
    assert set(payload) == {"provider", "provider_symbol", "start", "end", "analysis_date", "date_convention", "observation_kind", "coverage", "observations"}
    assert (payload["provider"], payload["provider_symbol"], payload["start"], payload["end"], payload["analysis_date"]) == ("finnhub", "TEST", START.isoformat(), END.isoformat(), ANALYSIS.isoformat())
    assert payload["date_convention"] == "utc-reference-day/vendor-date-labels"
    assert payload["coverage"] == "not_asserted" and payload["observation_kind"] == "upcoming_release_eps_estimate"
    assert [item["estimate"] for item in payload["observations"]] == ["1.250000000000000001", "0", "-0.25", None]
    for index, item in enumerate(payload["observations"]):
        assert item == {"symbol": "TEST", "fiscal_year": 2026, "fiscal_quarter": index + 1,
            "release_date": "2026-10-20", "release_session": "amc", "estimate": item["estimate"],
            "retrieved_at": "2026-10-17T20:00:00.123456Z", "provider": "finnhub", "source": "earnings_calendar",
            "source_field": "epsEstimate", "accounting_basis": "non-GAAP", "units": "currency-per-share",
            "currency": None, "share_basis": None, "published_at": None, "fiscal_period_end": None}
    assert rig.calls == ["date", "source", ("TEST", dict(start=START, end=END, analysis_date=ANALYSIS))]


def test_empty_is_not_zero_or_invalid_company_and_timestamp_does_not_round(rig):
    rig.result = ()
    assert request(rig.app)[1]["observations"] == []
    rig.result = (observation(estimate=Decimal("-0.000"), retrieved_at=STAMP.replace(microsecond=1)),)
    value = request(rig.app)[1]["observations"][0]
    assert value["estimate"] == "-0.000" and value["retrieved_at"] == "2026-10-17T20:00:00.000001Z"
    rig.result = (observation(),)
    assert request(rig.app)[1]["observations"][0]["retrieved_at"] == "2026-10-17T20:00:00Z"


@pytest.mark.parametrize("query", [
    b"", b"provider_symbol=TEST", QUERY + b"&unknown=x", QUERY + b"&end=2027-01-17",
    QUERY.replace(b"provider_symbol", b"symbol"), QUERY + b"&analysis_date=2026-10-17",
    QUERY + b"&", b"&" + QUERY, QUERY + b"&&x=1", QUERY + b"&bare", QUERY + b"&=x",
    QUERY.replace(b"TEST", b""), QUERY.replace(b"TEST", b"test"), QUERY.replace(b"TEST", b"+TEST"),
    QUERY.replace(b"TEST", b"TEST%20"), QUERY.replace(b"TEST", b"A/B"), QUERY.replace(b"TEST", b".A"),
    QUERY.replace(b"TEST", b"A" * 33), QUERY.replace(b"TEST", b"%FF"), QUERY.replace(b"TEST", b"%"),
    QUERY.replace(b"TEST", b"%A"), QUERY.replace(b"TEST", b"%GG"), QUERY.replace(b"TEST", b"\xff"),
    QUERY.replace(b"TEST", b"A%00"), QUERY.replace(b"TEST", b"A%0A"),
    QUERY.replace(b"2026-10-18", b"2026-1-18"), QUERY.replace(b"2026-10-18", b"2026-02-30"),
    QUERY.replace(b"2026-10-18", b"0000-10-18"), QUERY.replace(b"2026-10-18", b"2027-01-18"),
    QUERY.replace(b"2027-01-17", b"2027-01-18"), QUERY.replace(b"2026-10-18", b"2026-10-18T00:00:00"),
])
def test_query_grammar_and_span_before_date_or_provider(rig, query):
    assert request(rig.app, query)[0] == 422
    assert rig.calls == []


@pytest.mark.parametrize("symbol", ["A", "BRK.B", "ABC-1", "9" + "A" * 31])
def test_http_symbol_is_explicit_case_sensitive_and_not_a_lookup(rig, symbol):
    rig.result = ()
    assert request(rig.app, QUERY.replace(b"TEST", symbol.encode()))[0] == 200
    assert rig.calls[-1][0] == symbol


def test_disabled_and_rejected_requests_never_acquire_dependencies(rig):
    app = create_app(token=credential(), services=ApiServices(upcoming_eps=rig.service))
    assert request(app)[0:2] == (503, {"error": {"code": "eps_disabled", "message": "Upcoming EPS acquisition is disabled."}})
    assert request(app, QUERY + b"&x=1")[0] == 422
    assert rig.calls == []


@pytest.mark.parametrize("kind,status", [("auth", 401), ("host", 400), ("origin", 403),
    ("body", 422), ("chunk", 422), ("method", 405), ("target", 414)])
def test_access_boundary_before_all_dependencies(rig, kind, status):
    target = scope(PATH, query=QUERY, headers=authorized_headers())
    kwargs = {}
    if kind == "auth":
        target["headers"] = target["headers"][:1]
    elif kind == "host":
        target["headers"][0] = (b"host", b"outside.invalid")
    elif kind == "origin":
        target["headers"].append((b"origin", b"null"))
    elif kind == "body":
        target["headers"].append((b"content-length", b"1"))
    elif kind == "chunk":
        kwargs["messages"] = [{"type": "http.request", "body": b"synthetic-private", "more_body": True}]
    elif kind == "method":
        target["method"] = "POST"
    else:
        target["raw_path"] = b"/" + b"x" * 2048
    assert _loop.run_until_complete(invoke(rig.app, target, **kwargs))[0] == status
    assert rig.calls == []


@pytest.mark.parametrize("path", ["/api/v1/research/other", PATH + "/", PATH + "/history", "/health", "/api/v1/openapi.json"])
def test_exact_query_exception_does_not_enable_research_prefix(rig, path):
    result = _loop.run_until_complete(invoke(rig.app, scope(path, query=QUERY, headers=authorized_headers())))
    assert result[0] in (404, 422) and rig.calls == []


@pytest.mark.parametrize("value,status,code", [(START, 422, "invalid_request"),
    (END, 422, "invalid_request"), (None, 503, "provider_unavailable"),
    (True, 503, "provider_unavailable"), (STAMP, 503, "provider_unavailable")])
def test_local_input_and_broken_supplier_are_distinct(rig, value, status, code):
    rig.analysis_date = value
    result = request(rig.app)
    assert result[0] == status and result[1]["error"]["code"] == code
    assert rig.calls == ["date"]


@pytest.mark.parametrize("category,status,code", [(errors.ProviderRequestError, 503, "provider_unavailable"),
    (errors.ProviderAuthenticationError, 503, "provider_unavailable"), (errors.ProviderAccessError, 503, "provider_unavailable"),
    (errors.ProviderUnavailableError, 503, "provider_unavailable"), (errors.RateLimitError, 429, "provider_rate_limited"),
    (errors.ProviderTimeoutError, 504, "provider_timeout"), (errors.ProviderResponseError, 502, "provider_response_invalid")])
def test_upstream_errors_remain_sanitized(rig, category, status, code, caplog):
    rig.error = category()
    result = request(rig.app)
    assert result[0] == status and result[1]["error"]["code"] == code
    assert len(rig.calls) == 3 and "Traceback" not in caplog.text


@pytest.mark.parametrize("kind", ["wrong_symbol", "wrong_range", "forged", "metadata", "missing"])
def test_service_result_revalidated_and_bound_to_request(kind):
    view = UpcomingEpsView("TEST", START, END, ANALYSIS, (observation(),))
    if kind == "wrong_symbol":
        view = UpcomingEpsView("OTHER", START, END, ANALYSIS, ())
    elif kind == "wrong_range":
        view = UpcomingEpsView("TEST", START, END - timedelta(days=1), ANALYSIS, ())
    elif kind == "forged":
        view = object()
    elif kind == "metadata":
        object.__setattr__(view.observations[0], "currency", "USD")
    service = None if kind == "missing" else SimpleNamespace(upcoming_eps=lambda *args, **kwargs: view)
    app = create_app(token=credential(), services=ApiServices(upcoming_eps=service, upcoming_eps_enabled=True))
    assert request(app)[0:2] == (500, {"error": {"code": "internal_error", "message": "The operation failed."}})


def test_eps_slot_independent_of_history_but_shares_four_total_slots():
    app = create_app()
    admission = app.state.api_admission
    admission.reserve(False, eps=True)
    with pytest.raises(ApiFailure, match="capacity"):
        admission.reserve(False, eps=True)
    admission.reserve(True)
    admission.reserve(False)
    admission.reserve(False)
    with pytest.raises(ApiFailure, match="capacity"):
        admission.reserve(False)
    admission.release(False, eps=True)
    admission.reserve(False, eps=True)
    admission.release(False, eps=True)
    admission.release(True)
    admission.release(False)
    admission.release(False)
    assert (admission._active, admission._history, admission._eps) == (0, 0, 0)


def test_shared_capacity_refusal_precedes_research_date_and_provider(rig):
    admission = rig.app.state.api_admission
    for _ in range(4):
        admission.reserve(False)
    try:
        result = request(rig.app)
        assert result[0] == 503 and result[1]["error"]["code"] == "api_busy"
        assert rig.calls == []
    finally:
        for _ in range(4):
            admission.release(False)


def test_actual_eps_route_cancellation_holds_slot_until_worker_completion(rig):
    async def scenario():
        started, release = threading.Event(), threading.Event()
        def get(symbol, **kwargs):
            started.set()
            assert release.wait(5)
            return ()
        service = UpcomingEpsService(lambda: SimpleNamespace(get_upcoming_eps=get), research_date=lambda: ANALYSIS)
        app = create_app(token=credential(), services=ApiServices(upcoming_eps=service, upcoming_eps_enabled=True))
        operation = asyncio.create_task(invoke(app, scope(PATH, query=QUERY, headers=authorized_headers())))
        assert await asyncio.to_thread(started.wait, 5)
        operation.cancel()
        with pytest.raises(asyncio.CancelledError):
            await operation
        try:
            busy = await invoke(app, scope(PATH, query=QUERY, headers=authorized_headers()))
            assert busy[0] == 503 and busy[1]["error"]["code"] == "api_busy"
            assert app.state.api_admission._active == app.state.api_admission._eps == 1
        finally:
            release.set()
        await asyncio.gather(*(asyncio.all_tasks() - {asyncio.current_task()}))
        assert (await invoke(app, scope(PATH, query=QUERY, headers=authorized_headers())))[0] == 200
    _loop.run_until_complete(scenario())


def test_closed_asgi_client_cannot_release_eps_slot_while_provider_runs():
    async def scenario():
        started, release = threading.Event(), threading.Event()
        def get(symbol, **kwargs):
            started.set()
            assert release.wait(5)
            return ()
        service = UpcomingEpsService(lambda: SimpleNamespace(get_upcoming_eps=get), research_date=lambda: ANALYSIS)
        app = create_app(token=credential(), services=ApiServices(upcoming_eps=service, upcoming_eps_enabled=True))
        incoming = asyncio.Queue()
        await incoming.put({"type": "http.request", "body": b""})
        closed, sent = False, []
        async def send(message):
            if closed:
                raise OSError("Synthetic ASGI client disconnected")
            sent.append(message)
        first = asyncio.create_task(app(scope(PATH, query=QUERY, headers=authorized_headers()), incoming.get, send))
        assert await asyncio.to_thread(started.wait, 5)
        closed = True
        await incoming.put({"type": "http.disconnect"})
        try:
            busy = await invoke(app, scope(PATH, query=QUERY, headers=authorized_headers()))
            assert busy[0] == 503 and busy[1]["error"]["code"] == "api_busy"
            assert not first.done() and sent == []
        finally:
            release.set()
        await first
        assert sent == [] and app.state.api_admission._active == app.state.api_admission._eps == 0
        assert (await invoke(app, scope(PATH, query=QUERY, headers=authorized_headers())))[0] == 200
    _loop.run_until_complete(scenario())


def test_canceled_queued_eps_work_cannot_later_acquire_dependencies(monkeypatch):
    async def scenario():
        app = create_app()
        gate, started = threading.Event(), threading.Event()
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_running_loop()
        original = loop.run_in_executor
        submitted = asyncio.Event()
        def occupied():
            started.set()
            assert gate.wait(5)
        blocker = executor.submit(occupied)
        assert started.wait(5)
        def queued(ignored, callback, *args):
            future = original(executor, callback, *args)
            submitted.set()
            return future
        monkeypatch.setattr(loop, "run_in_executor", queued)
        calls = []
        operation = asyncio.create_task(run_data_operation(app, lambda: calls.append(True), eps=True))
        await asyncio.wait_for(submitted.wait(), 5)
        operation.cancel()
        with pytest.raises(asyncio.CancelledError):
            await operation
        assert app.state.api_admission._active == app.state.api_admission._eps == 0
        gate.set()
        await asyncio.gather(*(asyncio.all_tasks() - {asyncio.current_task()}))
        blocker.result(5)
        executor.shutdown(wait=True)
        assert calls == []
    _loop.run_until_complete(scenario())


def test_schema_exact_required_parameters_and_integer_bounds():
    document = create_app().openapi()
    parameters = document["paths"][PATH]["get"]["parameters"]
    assert [(item["name"], item["required"]) for item in parameters] == [("provider_symbol", True), ("start", True), ("end", True)]
    model = document["components"]["schemas"]["UpcomingEpsObservationResponse"]
    assert model["additionalProperties"] is False and set(model["required"]) == set(model["properties"])
    for field, bounds in (("fiscal_year", (1, 9999)), ("fiscal_quarter", (1, 4))):
        value = model["properties"][field]
        assert (value["minimum"], value["maximum"]) == bounds
        assert type(value["minimum"]) is type(value["maximum"]) is int
