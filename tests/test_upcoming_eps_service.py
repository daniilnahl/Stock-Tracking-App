"""Fixed-date service admission and untrusted provider-result boundaries."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from stock_tracker import exceptions as errors
from stock_tracker.providers.eps import UpcomingEpsEstimate
from stock_tracker.services import UpcomingEpsService, UpcomingEpsView


ANALYSIS, START, END = date(2026, 10, 16), date(2026, 10, 17), date(2027, 3, 1)
STAMP = datetime(2026, 10, 16, tzinfo=timezone.utc)


def observation(**overrides):
    return UpcomingEpsEstimate(**{**dict(symbol="TEST", fiscal_year=2026, fiscal_quarter=3,
        release_date=date(2026, 10, 20), release_session=None,
        estimate=Decimal("1.250000000000000001"), retrieved_at=STAMP), **overrides})


@pytest.fixture
def rig():
    state = SimpleNamespace(events=[], result=(observation(),), analysis_date=ANALYSIS,
                            source_error=None, provider_error=None)
    def research_date():
        state.events.append("date")
        return state.analysis_date
    def source():
        state.events.append("source")
        if state.source_error is not None:
            raise state.source_error
        def get_upcoming_eps(symbol, **kwargs):
            state.events.append((symbol, kwargs))
            if state.provider_error is not None:
                raise state.provider_error
            return state.result
        return SimpleNamespace(get_upcoming_eps=get_upcoming_eps)
    state.service = UpcomingEpsService(source, research_date=research_date)
    return state


def fetch(rig, **overrides):
    arguments = {**dict(symbol="TEST", start=START, end=END), **overrides}
    return rig.service.upcoming_eps(**arguments)


def test_exact_immutable_request_and_numeric_observations(rig):
    rig.result = tuple(observation(fiscal_quarter=index + 1, estimate=value)
                       for index, value in enumerate((Decimal("1.250000000000000001"),
                                                     Decimal(0), Decimal("-0.25"), None)))
    view = fetch(rig)
    assert view.observations is rig.result
    assert all(actual is supplied for actual, supplied in zip(view.observations, rig.result))
    assert (view.symbol, view.start, view.end, view.analysis_date) == ("TEST", START, END, ANALYSIS)
    assert rig.events == ["date", "source", ("TEST", dict(start=START, end=END, analysis_date=ANALYSIS))]
    assert [item.estimate for item in view.observations] == [Decimal("1.250000000000000001"), Decimal(0), Decimal("-0.25"), None]
    for item in view.observations:
        assert (item.provider, item.source, item.source_field) == ("finnhub", "earnings_calendar", "epsEstimate")
        assert item.accounting_basis == "non-GAAP" and item.units == "currency-per-share"
        assert item.currency is item.share_basis is item.published_at is item.fiscal_period_end is None
    with pytest.raises(FrozenInstanceError):
        view.analysis_date = START
    with pytest.raises(FrozenInstanceError):
        view.observations[0].estimate = Decimal(2)


def test_empty_result_has_context_and_no_extra_calls(rig):
    rig.result = ()
    view = fetch(rig)
    assert view.observations == () and view.analysis_date == ANALYSIS
    assert len(rig.events) == 3


def test_date_sampled_once_per_request_without_system_clock(rig):
    fetch(rig)
    rig.analysis_date = date(2026, 10, 15)
    view = fetch(rig)
    assert view.analysis_date == rig.analysis_date
    assert rig.events.count("date") == rig.events.count("source") == 2


@pytest.mark.parametrize("symbol", [None, True, "", "test", "TEST ", "A B", "A,B", "A\nB", "A" + chr(0xD800)])
def test_bad_symbol_before_date_or_provider(rig, symbol):
    with pytest.raises(errors.ProviderRequestError):
        fetch(rig, symbol=symbol)
    assert rig.events == []


@pytest.mark.parametrize("start,end", [(None, END), (START, None), (True, END),
    (START, False), (STAMP, END), (START, STAMP), (END, START), ("2026-10-17", END)])
def test_bad_bounds_before_date_or_provider(rig, start, end):
    with pytest.raises(errors.ProviderRequestError):
        fetch(rig, start=start, end=end)
    assert rig.events == []


@pytest.mark.parametrize("research_date", [START, END])
def test_invalid_intended_date_before_provider(rig, research_date):
    rig.analysis_date = research_date
    with pytest.raises(errors.ProviderRequestError):
        fetch(rig)
    assert rig.events == ["date"]


@pytest.mark.parametrize("research_date", [None, True, "2026-10-16", STAMP])
def test_malformed_date_supplier_is_dependency_failure(rig, research_date):
    rig.analysis_date = research_date
    with pytest.raises(errors.ProviderUnavailableError):
        fetch(rig)
    assert rig.events == ["date"]


def test_per_request_analysis_override_is_not_a_service_surface(rig):
    with pytest.raises(TypeError):
        rig.service.upcoming_eps("TEST", start=START, end=END, analysis_date=ANALYSIS)
    assert rig.events == []


def test_inclusive_single_release_date_and_different_fiscal_year(rig):
    rig.result = (observation(release_date=START, fiscal_year=2025),)
    view = fetch(rig, end=START)
    assert view.start == view.end == view.observations[0].release_date
    assert view.observations[0].fiscal_year == 2025


@pytest.mark.parametrize("result", [None, [], [observation()], iter((observation(),)),
    (None,), ({"estimate": 1},), (object(),)])
def test_result_must_be_immutable_typed_tuple(rig, result):
    rig.result = result
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)
    assert len(rig.events) == 3


@pytest.mark.parametrize("field,value", [
    ("symbol", "OTHER"), ("release_date", ANALYSIS), ("release_date", END + timedelta(days=1)),
    ("fiscal_year", True), ("fiscal_year", 0), ("fiscal_quarter", 5), ("fiscal_quarter", "3"),
    ("release_session", "unknown"), ("estimate", 1.25), ("estimate", True),
    ("estimate", Decimal("NaN")), ("estimate", Decimal("Infinity")),
    ("retrieved_at", STAMP.replace(tzinfo=None)), ("retrieved_at", None),
    ("provider", "other"), ("source", "company_earnings"), ("source_field", "epsActual"),
    ("accounting_basis", "GAAP"), ("units", "percentage"), ("currency", "USD"),
    ("share_basis", "diluted"), ("published_at", STAMP), ("fiscal_period_end", ANALYSIS),
])
def test_mutated_provider_models_are_revalidated(rig, field, value):
    malformed = observation()
    object.__setattr__(malformed, field, value)
    rig.result = (malformed,)
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)


@pytest.mark.parametrize("field", ["symbol", "estimate", "currency", "provider", "fiscal_year"])
def test_incomplete_provider_models_fail_safely(rig, field):
    malformed = observation()
    object.__delattr__(malformed, field)
    rig.result = (malformed,)
    with pytest.raises(errors.ProviderResponseError) as caught:
        fetch(rig)
    assert caught.value.__context__ is None or caught.value.__suppress_context__


def test_subclass_cannot_bypass_model_validation(rig):
    class UntrustedEstimate(UpcomingEpsEstimate):
        def __post_init__(self):
            pass
    rig.result = (UntrustedEstimate("TEST", 2026, 3, START, None, Decimal(0), STAMP),)
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)


@pytest.mark.parametrize("rows", [
    (observation(), observation(release_date=date(2026, 10, 21))),
    (observation(fiscal_quarter=4), observation()),
    (observation(release_date=date(2026, 10, 21)), observation(fiscal_quarter=4)),
])
def test_duplicate_or_unordered_observations_fail_without_repair(rig, rows):
    rig.result = rows
    with pytest.raises(errors.ProviderResponseError):
        fetch(rig)
    assert rig.result is rows


@pytest.mark.parametrize("error_type", [errors.ProviderAccessError, errors.ProviderAuthenticationError,
    errors.ProviderRequestError, errors.ProviderResponseError, errors.ProviderTimeoutError,
    errors.ProviderUnavailableError, errors.RateLimitError])
@pytest.mark.parametrize("stage", ["source", "provider"])
def test_provider_errors_preserved_without_retry(rig, stage, error_type):
    error = error_type()
    setattr(rig, stage + "_error", error)
    with pytest.raises(error_type) as caught:
        fetch(rig)
    assert caught.value is error
    assert rig.events.count("date") == rig.events.count("source") == 1
    assert len(rig.events) == (2 if stage == "source" else 3)


@pytest.mark.parametrize("provider", [None, object(), SimpleNamespace(get_upcoming_eps=3)])
def test_bad_acquired_provider_rejected(provider):
    service = UpcomingEpsService(lambda: provider, research_date=lambda: ANALYSIS)
    with pytest.raises(errors.ProviderResponseError):
        service.upcoming_eps("TEST", start=START, end=END)


def test_unexpected_dependency_errors_not_swallowed(rig):
    rig.provider_error = RuntimeError("synthetic-programming-error")
    with pytest.raises(RuntimeError) as caught:
        fetch(rig)
    assert caught.value is rig.provider_error


@pytest.mark.parametrize("changes", [dict(symbol="OTHER"), dict(start=END),
    dict(end=ANALYSIS), dict(analysis_date=START), dict(analysis_date=STAMP), dict(observations=[])])
def test_direct_view_construction_enforces_context(changes):
    candidate = UpcomingEpsView("TEST", START, END, ANALYSIS, (observation(),))
    with pytest.raises(errors.ProviderResponseError):
        replace(candidate, **changes)


def test_constructor_is_lazy_and_requires_callables():
    def denied():
        pytest.fail("Constructor invoked dependency")
    UpcomingEpsService(denied, research_date=denied)
    with pytest.raises(ValueError):
        UpcomingEpsService(None, research_date=denied)
    with pytest.raises(ValueError):
        UpcomingEpsService(denied, research_date=None)


def test_cold_source_service_probe(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(root / "tests/upcoming_eps_service_probe.py"), str(root / "src")],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
