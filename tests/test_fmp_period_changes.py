"""Synthetic Stable price-change schema, official docs inspected 2026-10-04.

Source: https://site.financialmodelingprep.com/developer/docs/stable/quote-change
Values are provider-reported percentage points, never reconstructed history.
"""

from datetime import datetime, timezone
from decimal import Decimal
import json
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest


FIELDS = [('1D', 'day_1'), ('5D', 'day_5'), ('1M', 'month_1'), ('3M', 'month_3'),
          ('6M', 'month_6'), ('1Y', 'year_1'), ('3Y', 'year_3'), ('5Y', 'year_5')]


@pytest.fixture
def rig():
    from stock_tracker.providers.fmp import FMPMarketDataProvider
    from stock_tracker.providers.transport import HttpResponse, ProviderPolicy
    state = SimpleNamespace(body=b'[{"symbol":"AAPL","1D":-1.234567890123456789,"5D":0,"1M":12.5,"3M":-3,"6M":6,"1Y":10.25,"3Y":33,"5Y":55}]',
                            status=200, requests=[], receipt=datetime(2020, 1, 2, tzinfo=timezone.utc))
    def get(url, *, headers, timeout_seconds):
        state.requests.append((url, headers, timeout_seconds))
        return HttpResponse(state.status, {}, state.body)
    policy = ProviderPolicy(10.0, 2, frozenset({408, 500, 502, 503, 504}),
                            0.5, 2.0, 30.0, False, 0.0, 0.0, False)
    dummy = 'synthetic-period-fixture'
    state.provider = FMPMarketDataProvider(api_key=dummy, transport=SimpleNamespace(get=get),
        policy=policy, clock=lambda: state.receipt, monotonic=lambda: 0.0,
        sleep=lambda delay: None, jitter=lambda upper: 0.0)
    state.row = lambda row: setattr(state, 'body', json.dumps([row]).encode())
    return state


def test_all_eight_fields_preserve_percentage_points_precision_and_request(rig):
    from stock_tracker.providers.models import PeriodChanges
    result = rig.provider.get_period_changes(' aapl ')
    assert isinstance(result, PeriodChanges) and result.symbol == 'AAPL'
    assert [getattr(result, field) for _, field in FIELDS] == [Decimal('-1.234567890123456789'),
        Decimal(0), Decimal('12.5'), Decimal(-3), Decimal(6), Decimal('10.25'), Decimal(33), Decimal(55)]
    assert result.as_of is None and result.retrieved_at == rig.receipt
    assert not hasattr(result, 'close') and not hasattr(result, 'date')
    assert len(rig.requests) == 1
    url, headers, timeout = rig.requests[0]
    assert urlsplit(url).path == '/stable/stock-price-change'
    assert parse_qs(urlsplit(url).query) == {'symbol': ['AAPL']}
    assert headers == {'apikey': 'synthetic-period-fixture'} and timeout == 10.0
    assert 'synthetic-' not in url + repr(result)


@pytest.mark.parametrize('key,field', FIELDS)
@pytest.mark.parametrize('present', [True, False])
def test_each_missing_or_null_field_remains_independently_none(rig, key, field, present):
    row = {'symbol': 'AAPL', **{item: 1 for item, _ in FIELDS}}
    if present:
        row[key] = None
    else:
        del row[key]
    rig.row(row)
    result = rig.provider.get_period_changes('AAPL')
    assert getattr(result, field) is None
    assert all(getattr(result, other) == Decimal(1) for _, other in FIELDS if other != field)


def test_all_unavailable_periods_are_valid_without_time_fabrication(rig):
    rig.row({'symbol': 'AAPL', 'timestamp': 'unverified', '10Y': 'ignored'})
    result = rig.provider.get_period_changes('AAPL')
    assert all(getattr(result, field) is None for _, field in FIELDS)
    assert result.as_of is None and result.retrieved_at == rig.receipt


@pytest.mark.parametrize('value', [0, -1, 10**30 + 1, -(10**30 + 1)])
def test_exact_signed_integer_values_are_not_rounded_or_scaled(rig, value):
    rig.row({'symbol': 'AAPL', '1D': value})
    assert rig.provider.get_period_changes('AAPL').day_1 == Decimal(value)


@pytest.mark.parametrize('key,field', FIELDS)
def test_malformed_any_period_rejects_whole_result(rig, key, field):
    from stock_tracker.exceptions import ProviderResponseError
    rig.row({'symbol': 'AAPL', **{item: 1 for item, _ in FIELDS}, key: 'synthetic-private-value'})
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_period_changes('AAPL')
    assert caught.value.field == field and 'synthetic-' not in str(caught.value)
    assert len(rig.requests) == 1


@pytest.mark.parametrize('value', [True, False, [], {}, '12.5'])
def test_present_wrong_type_late_field_is_malformed(rig, value):
    from stock_tracker.exceptions import ProviderResponseError
    rig.row({'symbol': 'AAPL', '1D': 12.5, '5Y': value})
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_period_changes('AAPL')
    assert caught.value.field == 'year_5'


@pytest.mark.parametrize('literal', ['NaN', 'Infinity', '-Infinity', '1e999999999999999999999999999'])
def test_nonfinite_or_unrepresentable_numbers_map_to_safe_response_error(rig, literal):
    from stock_tracker.exceptions import ProviderResponseError
    rig.body = ('[{"symbol":"AAPL","1D":1,"5Y":' + literal + '}]').encode()
    with pytest.raises(ProviderResponseError):
        rig.provider.get_period_changes('AAPL')
    assert len(rig.requests) == 1


@pytest.mark.parametrize('body', [b'[]', b'{}', b'[1]', b'{"error":"synthetic-private"}',
    b'[{"1D":1}]', b'[{"symbol":"MSFT"}]', b'[{"symbol":"aapl"}]',
    b'[{"symbol":" AAPL "}]', b'[{"symbol":null}]', b'[{"symbol":"AAPL"},{"symbol":"AAPL"}]'])
def test_empty_vs_malformed_shape_and_exact_identity(rig, body):
    from stock_tracker.exceptions import MarketDataUnavailableError, ProviderResponseError
    rig.body = body
    with pytest.raises(MarketDataUnavailableError if body == b'[]' else ProviderResponseError):
        rig.provider.get_period_changes('AAPL')
    assert len(rig.requests) == 1


@pytest.mark.parametrize('symbol', [None, True, '', ' ', 'AA PL', 'AA\x00PL', 'AAPL,MSFT'])
def test_invalid_symbol_precedes_io(rig, symbol):
    from stock_tracker.exceptions import InvalidTickerError
    with pytest.raises(InvalidTickerError):
        rig.provider.get_period_changes(symbol)
    assert rig.requests == []


@pytest.mark.parametrize('status,name,attempts', [(401, 'ProviderAuthenticationError', 1),
    (403, 'ProviderAccessError', 1), (404, 'ProviderUnavailableError', 1),
    (429, 'RateLimitError', 1), (500, 'ProviderUnavailableError', 2)])
def test_summary_preserves_common_failure_classifications(rig, status, name, attempts):
    import stock_tracker.exceptions as errors
    rig.status = status
    with pytest.raises(getattr(errors, name)):
        rig.provider.get_period_changes('AAPL')
    assert len(rig.requests) == attempts
