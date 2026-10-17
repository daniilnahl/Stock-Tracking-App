"""Offline upcoming-release observations, never historical consensus or calculations."""

from dataclasses import FrozenInstanceError, asdict, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
import pickle
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest

from stock_tracker import exceptions as errors
from stock_tracker.providers.eps import UpcomingEpsEstimate, UpcomingEpsProvider
from stock_tracker.providers.finnhub import FinnhubUpcomingEpsProvider
from stock_tracker.providers.transport import HttpResponse, _TransportConnectionError, _TransportTimeout


STAMP = datetime(2026, 10, 16, 20, tzinfo=timezone.utc)
START, END, ANALYSIS = date(2026, 10, 17), date(2027, 3, 1), date(2026, 10, 16)
SYNTHETIC_CREDENTIAL = "synthetic-finnhub-fixture"


def row(**changes):
    return {**dict(symbol="TEST", date="2026-10-20", year=2026, quarter=3,
                   hour="amc", epsActual=None, epsEstimate=1.25), **changes}


@pytest.fixture
def rig():
    state = SimpleNamespace(calls=[], body=b'{"earningsCalendar":[]}', status=200, action=None)
    def get(url, **kwargs):
        state.calls.append((url, kwargs))
        if state.action is not None:
            raise state.action
        return HttpResponse(state.status, {}, state.body)
    state.options = dict(api_key=SYNTHETIC_CREDENTIAL, transport=SimpleNamespace(get=get),
                         clock=lambda: STAMP, timeout_seconds=5.0,
                         max_response_bytes=20000, max_rows=10)
    state.provider = FinnhubUpcomingEpsProvider(**state.options)
    state.load = lambda rows: setattr(state, "body", json.dumps({"earningsCalendar": rows}).encode())
    return state


def fetch(rig, **kwargs):
    return rig.provider.get_upcoming_eps("TEST", **{**dict(start=START, end=END, analysis_date=ANALYSIS), **kwargs})


def test_precise_signed_zero_missing_and_provenance(rig):
    rig.body = b'''{"earningsCalendar":[
        {"symbol":"TEST","date":"2027-02-01","year":2026,"quarter":4,"epsActual":null,"epsEstimate":null},
        {"symbol":"TEST","date":"2026-10-20","year":2026,"quarter":1,"epsActual":null,"epsEstimate":1.250000000000000001,"hour":"bmo"},
        {"symbol":"TEST","date":"2026-10-20","year":2026,"quarter":3,"epsActual":null,"epsEstimate":-0.25,"hour":"dmh"},
        {"symbol":"TEST","date":"2026-10-20","year":2026,"quarter":2,"epsActual":null,"epsEstimate":0,"hour":"amc"}]}'''
    observations = fetch(rig)
    assert [item.estimate for item in observations] == [Decimal("1.250000000000000001"), Decimal(0), Decimal("-0.25"), None]
    assert [item.fiscal_quarter for item in observations] == [1, 2, 3, 4]
    assert observations[-1].fiscal_year != observations[-1].release_date.year
    for item in observations:
        assert item.retrieved_at == STAMP
        data = asdict(item)
        assert data["provider"] == "finnhub" and data["source"] == "earnings_calendar"
        assert data["source_field"] == "epsEstimate"
        assert data["accounting_basis"] == "non-GAAP" and data["units"] == "currency-per-share"
        assert all(data[key] is None for key in ("currency", "share_basis", "published_at", "fiscal_period_end"))
    with pytest.raises(FrozenInstanceError):
        observations[0].estimate = Decimal(9)
    url, options = rig.calls[0]
    assert parse_qs(urlsplit(url).query) == {"symbol": ["TEST"], "from": [START.isoformat()], "to": [END.isoformat()], "international": ["false"]}
    assert options == {"headers": {"X-Finnhub-Token": SYNTHETIC_CREDENTIAL}, "timeout_seconds": 5.0}
    assert SYNTHETIC_CREDENTIAL not in url + repr(rig.provider)
    with pytest.raises(TypeError):
        pickle.dumps(rig.provider)
    provider: UpcomingEpsProvider = rig.provider
    assert provider is rig.provider


@pytest.mark.parametrize("actual", [0, -0.2, 1.0])
def test_actual_present_excluded_and_no_result_is_honest(rig, actual):
    rig.load([row(epsActual=actual)])
    assert fetch(rig) == ()
    rig.load([])
    assert fetch(rig) == ()
    assert len(rig.calls) == 2


@pytest.mark.parametrize("session", [None, "", "  ", "\t"])
def test_unknown_session_preserved(rig, session):
    rig.load([row(hour=session)])
    assert fetch(rig)[0].release_session is None


@pytest.mark.parametrize("field,value", [
    ("symbol", "OTHER"), ("symbol", None), ("date", "2026-10-16"),
    ("date", "2027-03-02"), ("date", "2026-02-30"), ("date", "20261020"),
    ("date", "2026-10-20T00:00:00"), ("date", None),
    ("quarter", 0), ("quarter", 5), ("quarter", True), ("quarter", 1.0),
    ("year", 0), ("year", 10000), ("year", True), ("year", "2026"),
    ("epsActual", True), ("epsActual", "1.0"), ("epsEstimate", False),
    ("epsEstimate", "1.0"), ("hour", "unknown"), ("hour", 1), ("hour", []),
])
def test_bad_rows_are_not_ignored_even_with_actual_present(rig, field, value):
    candidate = row(epsActual=0)
    candidate[field] = value
    rig.load([candidate])
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)
    assert len(rig.calls) == 1


@pytest.mark.parametrize("field", ["epsActual", "epsEstimate", "date", "symbol", "year", "quarter"])
def test_required_missing_field_is_not_null(rig, field):
    candidate = row()
    del candidate[field]
    rig.load([candidate])
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)


def test_duplicate_periods_are_ambiguous_even_if_released(rig):
    rig.load([row(), row(date="2026-10-21", epsActual=0)])
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)


@pytest.mark.parametrize("body", [b"\xff", b"{", b"[]", b"null", b'{}', b'{"error":"synthetic-private"}',
    b'{"earningsCalendar":null}', b'{"earningsCalendar":[1]}',
    b'{"earningsCalendar":[],"earningsCalendar":[]}',
    b'{"earningsCalendar":[],"ignored":NaN}', b'{"earningsCalendar":[],"ignored":Infinity}',
    b'{"earningsCalendar":[],"ignored":1e9999999999999999999999999999}',
    b'{"earningsCalendar":[],"ignored":' + b'9' * 4400 + b'}',
    b'{"earningsCalendar":' + b'[' * 1500 + b'0' + b']' * 1500 + b'}'])
def test_malformed_payload_safe(rig, body):
    rig.body = body
    with pytest.raises(errors.ProviderResponseError) as caught:
        fetch(rig)
    assert "synthetic-private" not in str(caught.value)
    assert caught.value.__context__ is None or caught.value.__suppress_context__


@pytest.mark.parametrize("field", ["epsActual", "epsEstimate"])
@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e9999999999999999999999999999"])
def test_nonfinite_and_unrepresentable_numbers(rig, field, number):
    rig.load([row()])
    payload = json.loads(rig.body)
    payload["earningsCalendar"][0][field] = "REPLACE"
    rig.body = json.dumps(payload).replace('"REPLACE"', number).encode()
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)


@pytest.mark.parametrize("status,expected", [(401, errors.ProviderAuthenticationError), (402, errors.ProviderAccessError),
    (403, errors.ProviderAccessError), (429, errors.RateLimitError), (408, errors.ProviderTimeoutError),
    (500, errors.ProviderUnavailableError), (599, errors.ProviderUnavailableError),
    (302, errors.ProviderRequestError), (404, errors.ProviderRequestError), (204, errors.ProviderRequestError)])
def test_status_categories_single_call(rig, status, expected):
    rig.status, rig.body = status, b"synthetic-private"
    with pytest.raises(expected) as caught:
        fetch(rig)
    assert len(rig.calls) == 1 and "synthetic-private" not in str(caught.value)


@pytest.mark.parametrize("error,expected", [(_TransportTimeout(), errors.ProviderTimeoutError),
    (_TransportConnectionError(retryable=True), errors.ProviderUnavailableError),
    (_TransportConnectionError(retryable=False), errors.ProviderUnavailableError)])
def test_transport_failure_without_retry(rig, error, expected):
    rig.action = error
    with pytest.raises(expected) as caught:
        fetch(rig)
    assert len(rig.calls) == 1 and caught.value.__suppress_context__


@pytest.mark.parametrize("arguments", [dict(start=ANALYSIS), dict(end=ANALYSIS),
    dict(analysis_date=START), dict(analysis_date=END), dict(start=None),
    dict(start=datetime(2026, 10, 20)), dict(analysis_date="2026-10-16")])
def test_admission_precedes_network(rig, arguments):
    with pytest.raises(errors.ProviderRequestError):
        fetch(rig, **arguments)
    assert not rig.calls


@pytest.mark.parametrize("symbol", [None, True, "", "test", "TEST ", "A B", "A,B", "A\nB", "A" + chr(0xD800)])
def test_symbol_requires_explicit_provider_symbol(rig, symbol):
    with pytest.raises(errors.ProviderRequestError):
        rig.provider.get_upcoming_eps(symbol, start=START, end=END, analysis_date=ANALYSIS)
    assert not rig.calls


@pytest.mark.parametrize("name,value", [("timeout_seconds", True), ("timeout_seconds", 1),
    ("timeout_seconds", 0.0), ("timeout_seconds", float("nan")), ("timeout_seconds", float("inf")),
    ("max_rows", 0), ("max_rows", True), ("max_response_bytes", 0), ("max_response_bytes", True),
    ("api_key", None), ("api_key", ""), ("api_key", "synthetic\nprivate"), ("api_key", "clé"),
    ("clock", None), ("transport", None)])
def test_constructor_bounds(rig, name, value):
    with pytest.raises(ValueError) as caught:
        FinnhubUpcomingEpsProvider(**{**rig.options, name: value})
    assert "synthetic\nprivate" not in str(caught.value)
    assert not rig.calls


def test_response_bytes_and_rows_bounded(rig):
    rig.load([row(), row(quarter=4)])
    rig.provider = FinnhubUpcomingEpsProvider(**{**rig.options, "max_rows": 1})
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)
    rig.provider = FinnhubUpcomingEpsProvider(**{**rig.options, "max_response_bytes": len(rig.body)-1})
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)
    rig.load([])
    rig.provider = FinnhubUpcomingEpsProvider(**{**rig.options, "max_response_bytes": len(rig.body)})
    assert fetch(rig) == ()


@pytest.mark.parametrize("name,value", [("fiscal_year", True), ("fiscal_quarter", 5),
    ("release_date", datetime(2026, 10, 20)), ("release_session", "AMС"),
    ("estimate", 1.25), ("estimate", Decimal("NaN")), ("estimate", Decimal("Infinity")),
    ("retrieved_at", STAMP.replace(tzinfo=None)),
    ("retrieved_at", STAMP.astimezone(timezone(timedelta(hours=1))))])
def test_model_cannot_bypass_validation(name, value):
    observation = UpcomingEpsEstimate("TEST", 2026, 3, START, None, Decimal(0), STAMP)
    with pytest.raises(errors.ProviderResponseError):
        replace(observation, **{name: value})


def test_construction_defers_clock_tls_and_network(rig, monkeypatch):
    import stock_tracker.providers.finnhub_transport as module
    def denied(*args, **kwargs):
        pytest.fail("constructor performed IO")
    monkeypatch.setattr(module.ssl, "create_default_context", denied)
    monkeypatch.setattr(module.certifi, "where", denied)
    monkeypatch.setattr(module, "build_opener", denied)
    transport = module.FinnhubHttpTransport(max_response_bytes=20000)
    FinnhubUpcomingEpsProvider(**{**rig.options, "transport": transport, "clock": denied})
    assert not rig.calls


def test_cold_source_provider_probe(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(root / "tests/finnhub_eps_probe.py"), str(root / "src")],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
