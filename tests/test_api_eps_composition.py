"""Opt-in launcher graph over real EPS service/adapter and synthetic HTTPS."""

import asyncio
from datetime import datetime, timezone
import io
import json
import pickle
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest

from stock_tracker.api import launcher
from stock_tracker.api.configuration import ApiConfigurationError, load_api_configuration
from stock_tracker.api.composition import create_local_app
from stock_tracker.exceptions import ProviderUnavailableError
from test_api_foundation import authorized_headers, credential, invoke, scope
from test_api_upcoming_eps import PATH, QUERY


SYNTHETIC_CREDENTIAL = "synthetic-composed-finnhub-key"
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


def options(tmp_path):
    return {name: str(tmp_path / name) for name in ("database", "history_cache", "menu_legacy", "evaluation_legacy")}


def request(app, path=PATH, *, query=QUERY, headers=None):
    return _loop.run_until_complete(invoke(app, scope(path, query=query,
        headers=authorized_headers() if headers is None else headers)))


@pytest.fixture
def rig(tmp_path, monkeypatch):
    import config
    import stock_tracker.api.composition as composition
    import stock_tracker.providers.finnhub_transport as native
    import ssl
    context = ssl.create_default_context()
    state = SimpleNamespace(now=0.0, civil=[], keys=[], calls=[], bounds=[], status=200,
        body=b'{"earningsCalendar":[{"symbol":"TEST","year":2026,"quarter":3,"date":"2026-10-20","epsActual":null,"epsEstimate":1.250000000000000001}]}')
    class Clock:
        @classmethod
        def now(cls, zone):
            assert zone is timezone.utc
            state.civil.append(True)
            return STAMP
    monkeypatch.setattr(composition, "datetime", Clock)
    monkeypatch.setattr(composition, "monotonic", lambda: state.now)
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    monkeypatch.setenv("FINNHUB_API_KEY", SYNTHETIC_CREDENTIAL)
    monkeypatch.setenv("FMP_API_KEY", "synthetic-distinct-fmp")
    monkeypatch.setattr(config.dotenv, "load_dotenv", lambda: pytest.fail("EPS used dotenv"))
    original = config.load_finnhub_configuration
    def load():
        state.keys.append(True)
        return original()
    monkeypatch.setattr(config, "load_finnhub_configuration", load)
    class Body(io.BytesIO):
        def read(self, size=-1):
            state.bounds.append(size)
            return super().read(size)
    def opened(request, *, timeout):
        state.calls.append((request, timeout))
        body = Body(state.body)
        body.status, body.headers = state.status, {}
        return body
    monkeypatch.setattr(native, "build_opener", lambda *args: SimpleNamespace(open=opened))
    monkeypatch.setattr(native.ssl, "create_default_context", lambda **kwargs: context)
    state.configuration = load_api_configuration(**options(tmp_path), enable_upcoming_eps=True)
    state.app = create_local_app(state.configuration)
    return state


def test_lazy_composition_startup_quiet_and_real_single_call(rig, tmp_path, caplog):
    assert rig.keys == rig.calls == rig.civil == []
    assert request(rig.app, "/health", query=b"")[0] == 200
    assert request(rig.app, "/api/v1/openapi.json", query=b"")[0] == 200
    assert rig.keys == rig.calls == rig.civil == []
    assert request(rig.app)[0:2] == (429, {"error": {"code": "eps_rate_limited", "message": "Upcoming EPS request budget is unavailable."}})
    assert rig.keys == rig.calls == [] and len(rig.civil) == 1
    rig.now = 60.0
    result = request(rig.app)
    assert result[0] == 200 and result[1]["analysis_date"] == "2026-10-17"
    assert result[1]["observations"][0]["estimate"] == "1.250000000000000001"
    assert result[1]["observations"][0]["retrieved_at"] == "2026-10-17T20:00:00Z"
    assert len(rig.keys) == len(rig.calls) == 1 and len(rig.civil) == 3
    outgoing, timeout = rig.calls[0]
    assert timeout == 5.0 and rig.bounds == [262145]
    assert outgoing.get_header("X-finnhub-token") == SYNTHETIC_CREDENTIAL
    assert parse_qs(urlsplit(outgoing.full_url).query) == {
        "symbol": ["TEST"], "from": ["2026-10-18"], "to": ["2027-01-17"], "international": ["false"]}
    assert SYNTHETIC_CREDENTIAL not in outgoing.full_url + caplog.text + repr(rig.app.state.api_services)
    assert not list(tmp_path.iterdir())


def test_local_date_and_access_rejections_precede_budget_key_or_provider(rig):
    assert request(rig.app, query=QUERY + b"&x=1")[0] == 422
    assert request(rig.app, query=QUERY.replace(b"2026-10-18", b"2026-10-17"))[0] == 422
    assert request(rig.app, headers=authorized_headers()[:1])[0] == 401
    assert rig.keys == rig.calls == []
    rig.now = 60.0
    assert request(rig.app)[0] == 200
    assert len(rig.keys) == 1


def test_disabled_never_constructs_budget_or_samples_civil_clock(rig, monkeypatch, tmp_path):
    import stock_tracker.api.composition as composition
    def denied(*args):
        pytest.fail("Disabled composition acquired EPS infrastructure")
    monkeypatch.setattr(composition, "EpsBudget", denied)
    config = load_api_configuration(**options(tmp_path))
    app = create_local_app(config)
    assert request(app)[1]["error"]["code"] == "eps_disabled"
    assert rig.keys == rig.calls == rig.civil == []


@pytest.mark.parametrize("key", [None, "", " ", "synthetic padded ", "synthetic\nprivate"])
def test_configuration_failures_count_attempts_without_active_lease(rig, monkeypatch, key):
    if key is None:
        monkeypatch.delenv("FINNHUB_API_KEY")
    else:
        monkeypatch.setenv("FINNHUB_API_KEY", key)
    rig.now = 60.0
    for _ in range(30):
        assert request(rig.app)[1]["error"]["code"] == "provider_unavailable"
    assert request(rig.app)[1]["error"]["code"] == "eps_rate_limited"
    assert len(rig.keys) == 30 and rig.calls == []
    monkeypatch.setenv("FINNHUB_API_KEY", SYNTHETIC_CREDENTIAL)
    rig.now = 120.0
    assert request(rig.app)[0] == 200


def test_factory_exception_releases_lease_but_consumes_attempt(rig, monkeypatch):
    import stock_tracker.providers.finnhub_factory as factory
    original = factory.create_upcoming_eps_provider
    monkeypatch.setattr(factory, "create_upcoming_eps_provider", lambda *args, **kwargs: (_ for _ in ()).throw(ProviderUnavailableError()))
    rig.now = 60.0
    assert request(rig.app)[1]["error"]["code"] == "provider_unavailable"
    monkeypatch.setattr(factory, "create_upcoming_eps_provider", original)
    assert request(rig.app)[0] == 200
    assert len(rig.keys) == 2 and len(rig.calls) == 1


def test_upstream_429_cooldown_and_all_other_failures_release_lease(rig):
    rig.now, rig.status = 60.0, 429
    assert request(rig.app)[1]["error"]["code"] == "provider_rate_limited"
    rig.status, rig.now = 200, 119.999999
    assert request(rig.app)[1]["error"]["code"] == "eps_rate_limited"
    assert len(rig.calls) == 1
    rig.now = 120.0
    assert request(rig.app)[0] == 200
    for status, expected in ((401, 503), (403, 503), (500, 503), (408, 504), (400, 503)):
        rig.status = status
        assert request(rig.app)[0] == expected
    rig.status, rig.body = 200, b'{"earningsCalendar":false}'
    assert request(rig.app)[0] == 502
    rig.body = b'{"earningsCalendar":[]}'
    assert request(rig.app)[0] == 200


def test_fixed_row_and_byte_bounds_and_provider_serialization(rig):
    from stock_tracker.providers.finnhub_factory import create_upcoming_eps_provider
    provider = create_upcoming_eps_provider(SYNTHETIC_CREDENTIAL, clock=lambda: STAMP)
    assert provider._max_rows == 128 and provider._max_response_bytes == 262144
    assert provider._transport._max_response_bytes == 262144 and provider._timeout_seconds == 5.0
    assert SYNTHETIC_CREDENTIAL not in repr(provider)
    with pytest.raises(TypeError):
        pickle.dumps(provider)
    rig.now, rig.body = 60.0, b"x" * 262145
    assert request(rig.app)[0] == 502
    rig.body = json.dumps({"earningsCalendar": [None] * 129}).encode()
    assert request(rig.app)[0] == 502
    rig.body = b'{"earningsCalendar":[]}'
    assert request(rig.app)[0] == 200


def test_composed_cancellation_keeps_native_work_and_budget_lease_until_completion(rig, monkeypatch):
    import stock_tracker.providers.finnhub_transport as native
    original = native.build_opener
    started, release = threading.Event(), threading.Event()
    def opener(*args):
        delegate = original(*args)
        def opened(*args, **kwargs):
            started.set()
            assert release.wait(5)
            return delegate.open(*args, **kwargs)
        return SimpleNamespace(open=opened)
    monkeypatch.setattr(native, "build_opener", opener)
    rig.now = 60.0
    async def scenario():
        task = asyncio.create_task(invoke(rig.app, scope(PATH, query=QUERY, headers=authorized_headers())))
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        try:
            busy = await invoke(rig.app, scope(PATH, query=QUERY, headers=authorized_headers()))
            assert busy[1]["error"]["code"] == "api_busy" and len(rig.keys) == 1
        finally:
            release.set()
        await asyncio.gather(*(asyncio.all_tasks() - {asyncio.current_task()}))
        assert (await invoke(rig.app, scope(PATH, query=QUERY, headers=authorized_headers())))[0] == 200
    _loop.run_until_complete(scenario())
    assert len(rig.keys) == len(rig.calls) == 2


def test_launch_flag_independent_defaults_duplicates_and_boolean_issuance(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    args = [item for name, value in options(tmp_path).items() for item in ("--" + name.replace("_", "-"), value)]
    assert launcher.parse_arguments(args)["enable_upcoming_eps"] is False
    parsed = launcher.parse_arguments([*args, "--enable-upcoming-eps"])
    assert parsed["enable_upcoming_eps"] is True and parsed["enable_history"] is parsed["enable_dashboard"] is False
    assert launcher.parse_arguments([*args, "--enable-upcoming-eps", "--enable-history", "--dashboard"])["enable_upcoming_eps"] is True
    with pytest.raises(SystemExit) as caught:
        launcher.parse_arguments([*args, "--enable-upcoming-eps", "--enable-upcoming-eps"])
    assert caught.value.code == 2
    for bad in (None, 0, 1, "true"):
        with pytest.raises(ApiConfigurationError):
            load_api_configuration(**options(tmp_path), enable_upcoming_eps=bad)
    config = load_api_configuration(**options(tmp_path), enable_upcoming_eps=True)
    object.__setattr__(config, "enable_upcoming_eps", "true")
    with pytest.raises(ApiConfigurationError):
        create_local_app(config)


def test_source_real_eps_launcher_composition_probe(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-I", "-B", str(root / "tests/eps_composition_probe.py"), str(root / "src")],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
