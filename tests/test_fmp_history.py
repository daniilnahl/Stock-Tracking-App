"""Synthetic raw Stable history fixtures; official guide reconfirmed 2026-10-08.

Schema: /stable/historical-price-eod/non-split-adjusted; adj* fields are RAW.
https://site.financialmodelingprep.com/how-to/fmp-historical-price-apis-from-light-charts-to-dividendadjusted-analysis
No fixture represents live entitlement, market facts or complete sessions.
"""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, localcontext
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest


START, END = date(2020, 1, 2), date(2020, 1, 6)
NOW = datetime(2020, 1, 7, 12, tzinfo=timezone.utc)


def row(session="2020-01-02", **changes):
    return dict(symbol="AAPL", date=session, adjOpen=100, adjHigh=120,
                adjLow=99, adjClose=110, volume=12) | changes


@pytest.fixture
def rig():
    from stock_tracker.providers.fmp import FMPMarketDataProvider
    from stock_tracker.providers.transport import HttpResponse, ProviderPolicy

    state = SimpleNamespace(body=json.dumps([row()]).encode(), statuses=[200], requests=[],
                            receipt=NOW, sleeps=[])
    def get(url, *, headers, timeout_seconds):
        state.requests.append((url, headers, timeout_seconds))
        status = state.statuses.pop(0) if len(state.statuses) > 1 else state.statuses[0]
        return HttpResponse(status, {"Retry-After": "3"}, state.body)
    dummy = "synthetic-history-fixture"
    state.provider = FMPMarketDataProvider(
        api_key=dummy, transport=SimpleNamespace(get=get),
        policy=ProviderPolicy(10.0, 2, frozenset({408, 500, 502, 503, 504}),
                              0.5, 2.0, 30.0, False, 0.0, 0.0, False),
        clock=lambda: state.receipt, monotonic=lambda: 0.0,
        sleep=state.sleeps.append, jitter=lambda upper: upper,
    )
    state.rows = lambda rows: setattr(state, "body", json.dumps(rows).encode())
    return state


def test_raw_precision_receipt_request_and_no_hidden_calls(rig):
    rig.body = b'[{"symbol":"AAPL","date":"2020-01-02","adjOpen":100.123456789012345678901234567890,"adjHigh":120,"adjLow":99,"adjClose":110.000000000000000001,"volume":12.0,"close":999,"adjusted_close":888}]'
    with localcontext() as context:
        context.prec = 3
        observed = rig.provider._load_price_history(" aapl ", START, END)
    bar, = observed.bars
    assert (bar.open, bar.high, bar.low, bar.close, bar.volume) == (
        Decimal("100.123456789012345678901234567890"), Decimal(120), Decimal(99),
        Decimal("110.000000000000000001"), 12)
    assert bar.open.as_tuple().exponent == -30
    assert bar.adjusted_close is None and observed.retrieved_at == NOW
    url, headers, timeout = rig.requests[0]
    assert len(rig.requests) == 1
    assert urlsplit(url).path == "/stable/historical-price-eod/non-split-adjusted"
    assert parse_qs(urlsplit(url).query) == {"symbol": ["AAPL"], "from": ["2020-01-02"], "to": ["2020-01-06"]}
    assert headers == {"apikey": "synthetic-history-fixture"} and timeout == 10.0
    assert "synthetic-" not in url
    with pytest.raises(FrozenInstanceError):
        observed.retrieved_at = NOW


def test_order_bounds_sparse_sessions_and_fresh_lists(rig):
    rig.rows([row("2020-01-07"), row("2020-01-06"), row("2020-01-01"), row()])
    bars = rig.provider.get_price_history("AAPL", START, END)
    assert [bar.date for bar in bars] == [START, END]
    bars.clear()
    assert len(rig.provider.get_price_history("AAPL", START, END)) == 2
    assert len(rig.requests) == 2


@pytest.mark.parametrize("volume", [None, 0, 9223372036854775807])
def test_zero_prices_and_nullable_bounded_volume(rig, volume):
    rig.rows([row(adjOpen=0, adjHigh=0, adjLow=0, adjClose=0, volume=volume)])
    bar, = rig.provider.get_price_history("AAPL", START, START)
    assert bar.open == bar.high == bar.low == bar.close == Decimal(0)
    assert bar.volume == volume and bar.adjusted_close is None
    rig.rows([{key: value for key, value in row().items() if key != "volume"}])
    assert rig.provider.get_price_history("AAPL", START, END)[0].volume is None


@pytest.mark.parametrize("start,end", [
    (None, END), (START, None), ("2020-01-02", END), (START, NOW),
    (True, END), (END, START), (START, date(2020, 1, 7)),
    (date(2009, 1, 1), END), (date.min, date.max),
])
def test_invalid_ranges_rejected_before_transport(rig, start, end):
    from stock_tracker.exceptions import HistoryRangeError
    with pytest.raises(HistoryRangeError) as caught:
        rig.provider.get_price_history("AAPL", start, end)
    assert str(caught.value) == "Historical date range is invalid."
    assert rig.requests == []


def test_inclusive_maximum_range_and_prior_utc_date(rig):
    start = END - timedelta(days=3659)
    rig.rows([row(start.isoformat())])
    assert rig.provider.get_price_history("AAPL", start, END)[0].date == start
    from stock_tracker.exceptions import HistoryRangeError
    with pytest.raises(HistoryRangeError):
        rig.provider.get_price_history("AAPL", start - timedelta(days=1), END)
    rig.receipt = datetime(2020, 3, 1, tzinfo=timezone.utc)
    rig.rows([row("2020-02-29")])
    assert rig.provider.get_price_history("AAPL", date(2020, 2, 29), date(2020, 2, 29))[0].date == date(2020, 2, 29)


@pytest.mark.parametrize("symbol", [None, 1, False, "", "  ", "AA PL", "AAPL,MSFT", "AA\x00PL"])
def test_invalid_symbols_rejected_without_lookup(rig, symbol):
    from stock_tracker.exceptions import InvalidTickerError
    with pytest.raises(InvalidTickerError):
        rig.provider.get_price_history(symbol, START, END)
    assert rig.requests == []


@pytest.mark.parametrize("field", ["adjOpen", "adjHigh", "adjLow", "adjClose"])
@pytest.mark.parametrize("value", [None, True, False, "100", -1, [], {}])
def test_invalid_required_numeric_fields_atomic_no_retry(rig, field, value):
    from stock_tracker.exceptions import ProviderResponseError
    rig.rows([row(), row("2020-01-06", **{field: value})])
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_price_history("AAPL", START, END)
    assert caught.value.field == field and len(rig.requests) == 1


@pytest.mark.parametrize("field", ["adjOpen", "adjHigh", "adjLow", "adjClose"])
def test_missing_required_price(rig, field):
    from stock_tracker.exceptions import ProviderResponseError
    fixture = row()
    del fixture[field]
    rig.rows([fixture])
    with pytest.raises(ProviderResponseError, match=f"invalid {field}"):
        rig.provider.get_price_history("AAPL", START, END)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "1e999999999999999999999999999", "-0.01"])
def test_nonfinite_or_invalid_decimal_literals(rig, value):
    from stock_tracker.exceptions import ProviderResponseError
    rig.body = json.dumps([row()]).replace('"adjOpen": 100', '"adjOpen": ' + value).encode()
    with pytest.raises(ProviderResponseError):
        rig.provider.get_price_history("AAPL", START, END)
    assert len(rig.requests) == 1


@pytest.mark.parametrize("volume", [True, False, -1, 1.5, "12", [], {}, 9223372036854775808])
def test_invalid_volume(rig, volume):
    from stock_tracker.exceptions import ProviderResponseError
    rig.rows([row(volume=volume)])
    with pytest.raises(ProviderResponseError, match="invalid volume"):
        rig.provider.get_price_history("AAPL", START, END)


def test_compact_exponent_volume_is_bounded_before_integer_conversion(rig):
    from stock_tracker.exceptions import ProviderResponseError
    rig.body = json.dumps([row()]).replace('"volume": 12', '"volume": 1e100000000').encode()
    with pytest.raises(ProviderResponseError, match="invalid volume"):
        rig.provider.get_price_history("AAPL", START, END)


@pytest.mark.parametrize("changes", [dict(adjOpen=121), dict(adjOpen=98), dict(adjClose=121),
                                    dict(adjClose=98), dict(adjHigh=98), dict(adjLow=121)])
def test_impossible_ohlc_rejected_even_outside_requested_range(rig, changes):
    from stock_tracker.exceptions import ProviderResponseError
    rig.rows([row(), row("2020-01-01", **changes)])
    with pytest.raises(ProviderResponseError):
        rig.provider.get_price_history("AAPL", START, END)


@pytest.mark.parametrize("value", [None, True, "20200102", "2020-W01-4", "2020-1-02",
                                  "2020-02-30", "2020-01-02T00:00:00", "2020-01-02 "])
def test_strict_session_date(rig, value):
    from stock_tracker.exceptions import ProviderResponseError
    rig.rows([row(date=value)])
    with pytest.raises(ProviderResponseError, match="invalid date"):
        rig.provider.get_price_history("AAPL", START, END)


@pytest.mark.parametrize("symbol", [None, "aapl", " AAPL ", "MSFT"])
def test_wrong_identity_even_outside_range(rig, symbol):
    from stock_tracker.exceptions import ProviderResponseError
    rig.rows([row(), row("2020-01-01", symbol=symbol)])
    with pytest.raises(ProviderResponseError, match="invalid symbol"):
        rig.provider.get_price_history("AAPL", START, END)


@pytest.mark.parametrize("session", ["2020-01-02", "2020-01-01"])
def test_duplicates_anywhere_rejected_without_deduplication(rig, session):
    from stock_tracker.exceptions import ProviderResponseError
    rig.rows([row(session), row(session)])
    with pytest.raises(ProviderResponseError, match="invalid date"):
        rig.provider.get_price_history("AAPL", START, END)


@pytest.mark.parametrize("body", [b'{}', b'null', b'[1]', b'[{"Error Message":"synthetic-private"}]',
                                  b'[{', b'\xff', b'[{},null]'])
def test_malformed_payload_safe_atomic_failure(rig, body, caplog):
    from stock_tracker.exceptions import ProviderResponseError
    rig.body = body
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_price_history("AAPL", START, END)
    assert "synthetic-" not in str(caught.value) + repr(caught.value) + caplog.text
    assert len(rig.requests) == 1


@pytest.mark.parametrize("rows", [[], [row("2020-01-01")]])
def test_empty_data_is_unavailable_not_invalid_symbol(rig, rows):
    from stock_tracker.exceptions import MarketDataUnavailableError
    rig.rows(rows)
    with pytest.raises(MarketDataUnavailableError):
        rig.provider.get_price_history("AAPL", START, END)
    assert len(rig.requests) == 1


def test_decoded_row_limit_rejects_whole_response(rig):
    from stock_tracker.exceptions import ProviderResponseError
    rig.rows([row()] * 5001)
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_price_history("AAPL", START, END)
    assert caught.value.field is None and len(rig.requests) == 1


def test_exact_decoded_row_limit_accepts_valid_outside_observations(rig):
    oldest = END - timedelta(days=4999)
    rig.rows([row((oldest + timedelta(days=offset)).isoformat()) for offset in range(5000)])
    bars = rig.provider.get_price_history("AAPL", START, END)
    assert [bar.date for bar in bars] == [START + timedelta(days=offset) for offset in range(5)]
    assert len(rig.requests) == 1


@pytest.mark.parametrize("status,error,attempts", [
    (400, "ProviderRequestError", 1), (401, "ProviderAuthenticationError", 1),
    (402, "ProviderAccessError", 1), (403, "ProviderAccessError", 1),
    (404, "ProviderUnavailableError", 1), (422, "ProviderRequestError", 1),
    (429, "RateLimitError", 1), (408, "ProviderUnavailableError", 2),
    (500, "ProviderUnavailableError", 2), (503, "ProviderUnavailableError", 2),
])
def test_existing_status_policy_no_fallback_or_secret_logs(rig, status, error, attempts, caplog):
    from stock_tracker import exceptions
    rig.statuses = [status]
    with pytest.raises(getattr(exceptions, error)) as caught:
        rig.provider.get_price_history("AAPL", START, END)
    assert len(rig.requests) == attempts
    assert len(rig.sleeps) == attempts - 1
    assert "synthetic-" not in repr(caught.value) + caplog.text
    assert len({request[0] for request in rig.requests}) == 1
    if status == 429:
        assert caught.value.retry_after_seconds == 3.0


def test_retry_success_retains_final_receipt(rig):
    rig.statuses = [503, 200]
    assert rig.provider._load_price_history("AAPL", START, END).retrieved_at == NOW
    assert len(rig.requests) == 2 and rig.sleeps == [0.5]


@pytest.mark.parametrize("failure,error,attempts", [
    ("timeout", "ProviderTimeoutError", 2), ("connection", "ProviderUnavailableError", 2),
    ("permanent", "ProviderUnavailableError", 1),
])
def test_history_transport_failures_keep_existing_retry_policy(rig, failure, error, attempts):
    from stock_tracker import exceptions
    from stock_tracker.providers.transport import _TransportConnectionError, _TransportTimeout
    def get(url, *, headers, timeout_seconds):
        rig.requests.append((url, headers, timeout_seconds))
        if failure == "timeout":
            raise _TransportTimeout()
        raise _TransportConnectionError(retryable=failure == "connection")
    rig.provider._transport = SimpleNamespace(get=get)
    with pytest.raises(getattr(exceptions, error)):
        rig.provider.get_price_history("AAPL", START, END)
    assert len(rig.requests) == attempts and len(rig.sleeps) == attempts - 1


@pytest.mark.parametrize("change", [dict(open=Decimal(98)), dict(close=Decimal(121)),
                                  dict(low=Decimal(121)), dict(high=Decimal(98))])
def test_price_bar_constructor_ohlc_invariants(change):
    from stock_tracker.providers.models import PriceBar
    from stock_tracker.exceptions import ProviderResponseError
    bar = PriceBar("AAPL", START, Decimal(100), Decimal(120), Decimal(99), Decimal(110), None, None)
    with pytest.raises(ProviderResponseError):
        replace(bar, **change)
    assert replace(bar, adjusted_close=Decimal(1000)).adjusted_close == Decimal(1000)


@pytest.mark.parametrize("case", ["list", "empty", "wrongbar", "reverse", "duplicate", "adjusted", "volume", "naive", "offset"])
def test_internal_observation_validates_receipt_and_raw_sequence(case):
    from stock_tracker.providers.models import HistoryObservation, PriceBar
    from stock_tracker.exceptions import ProviderResponseError
    bar = PriceBar("AAPL", START, Decimal(100), Decimal(120), Decimal(99), Decimal(110), None, None)
    later = replace(bar, date=END)
    bars, received = (bar,), NOW
    if case == "list":
        bars = [bar]
    if case == "empty":
        bars = ()
    if case == "wrongbar":
        bars = (None,)
    if case == "reverse":
        bars = (later, bar)
    if case == "duplicate":
        bars = (bar, bar)
    if case == "adjusted":
        bars = (replace(bar, adjusted_close=Decimal(1)),)
    if case == "volume":
        bars = (replace(bar, volume=9223372036854775808),)
    if case == "naive":
        received = NOW.replace(tzinfo=None)
    if case == "offset":
        received = NOW.replace(tzinfo=timezone(timedelta(hours=1)))
    with pytest.raises(ProviderResponseError):
        HistoryObservation(bars, received)


def test_programming_clock_failure_propagates_without_request(rig):
    rig.provider._clock = lambda: (_ for _ in ()).throw(RuntimeError("clock defect"))
    with pytest.raises(RuntimeError, match="clock defect"):
        rig.provider.get_price_history("AAPL", START, END)
    assert rig.requests == []


def test_source_offline_provider_integration_probe(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", str(root / "tests" / "provider_integration_probe.py"), str(root)],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
