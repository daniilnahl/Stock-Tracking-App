"""Synthetic Stable profile schema, official docs inspected 2026-10-04.

Source: https://site.financialmodelingprep.com/developer/docs/stable/profile-symbol
Stable uses marketCap; mktCap belongs to the legacy schema.
"""

from datetime import datetime, timezone
from decimal import Decimal
import json
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest


@pytest.fixture
def rig():
    from stock_tracker.providers.fmp import FMPMarketDataProvider
    from stock_tracker.providers.transport import HttpResponse, ProviderPolicy
    state = SimpleNamespace(body=b'[{"symbol":"AAPL","companyName":"Fictional company","price":123.123456789012345678,"marketCap":9876543210.123456789012,"exchange":"NASDAQ","currency":"USD","sector":"Technology","country":"US"}]',
                            status=200, requests=[], receipt=datetime(2020, 1, 2, tzinfo=timezone.utc))
    def get(url, *, headers, timeout_seconds):
        state.requests.append((url, headers, timeout_seconds))
        return HttpResponse(state.status, {}, state.body)
    policy = ProviderPolicy(10.0, 2, frozenset({408, 500, 502, 503, 504}),
                            0.5, 2.0, 30.0, False, 0.0, 0.0, False)
    dummy = 'synthetic-profile-fixture'
    state.provider = FMPMarketDataProvider(api_key=dummy, transport=SimpleNamespace(get=get),
        policy=policy, clock=lambda: state.receipt, monotonic=lambda: 0.0,
        sleep=lambda delay: None, jitter=lambda upper: 0.0)
    state.row = lambda row: setattr(state, 'body', json.dumps([row]).encode())
    state.minimal = {'symbol': 'AAPL', 'companyName': 'Fictional company', 'price': None, 'marketCap': None}
    return state


def test_full_profile_preserves_precision_and_single_request(rig):
    from stock_tracker.providers.models import CompanyProfile
    profile = rig.provider.get_company_profile(' aapl ')
    assert isinstance(profile, CompanyProfile)
    assert profile.symbol == 'AAPL' and profile.name == 'Fictional company'
    assert profile.price == Decimal('123.123456789012345678')
    assert profile.market_cap == Decimal('9876543210.123456789012')
    assert (profile.exchange, profile.currency, profile.sector, profile.country) == ('NASDAQ', 'USD', 'Technology', 'US')
    assert profile.as_of is None and profile.retrieved_at == rig.receipt
    assert len(rig.requests) == 1
    url, headers, timeout = rig.requests[0]
    assert urlsplit(url).path == '/stable/profile' and parse_qs(urlsplit(url).query) == {'symbol': ['AAPL']}
    assert headers == {'apikey': 'synthetic-profile-fixture'} and timeout == 10.0
    assert 'synthetic-' not in url and 'synthetic-' not in repr(profile)


def test_minimal_profile_has_no_inferred_metadata_or_market_time(rig):
    rig.row(dict(rig.minimal, timestamp='unverified-provider-field', future={'x': 1}))
    profile = rig.provider.get_company_profile('AAPL')
    assert profile.price is profile.market_cap is None
    assert profile.exchange is profile.currency is profile.sector is profile.country is profile.as_of is None
    assert profile.retrieved_at == rig.receipt and len(rig.requests) == 1


@pytest.mark.parametrize('value,expected', [(None, None), (0, Decimal(0)), (123, Decimal(123)),
                                            (10**30 + 1, Decimal(10**30 + 1))])
def test_nullable_numbers_preserve_zero_and_exact_int(rig, value, expected):
    rig.row(dict(rig.minimal, price=value, marketCap=value))
    profile = rig.provider.get_company_profile('AAPL')
    assert profile.price == profile.market_cap == expected


@pytest.mark.parametrize('symbol', [None, True, '', ' ', 'AA PL', 'AA\x00PL', 'AAPL,MSFT'])
def test_invalid_local_input_has_no_requests(rig, symbol):
    from stock_tracker.exceptions import InvalidTickerError
    with pytest.raises(InvalidTickerError):
        rig.provider.get_company_profile(symbol)
    assert rig.requests == []


@pytest.mark.parametrize('body', [b'[]', b'{}', b'[1]', b'{"error":"synthetic-private"}',
    b'[{"symbol":"AAPL","companyName":"Fictional","price":1,"marketCap":2},{"symbol":"MSFT"}]'])
def test_empty_malformed_and_multiple_rows(rig, body):
    from stock_tracker.exceptions import MarketDataUnavailableError, ProviderResponseError
    rig.body = body
    with pytest.raises(MarketDataUnavailableError if body == b'[]' else ProviderResponseError) as caught:
        rig.provider.get_company_profile('AAPL')
    assert 'synthetic-private' not in str(caught.value) and len(rig.requests) == 1


@pytest.mark.parametrize('symbol', ['MSFT', 'aapl', ' AAPL ', None, True])
def test_returned_identity_never_silently_repaired(rig, symbol):
    from stock_tracker.exceptions import ProviderResponseError
    rig.row(dict(rig.minimal, symbol=symbol))
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_company_profile('AAPL')
    assert caught.value.field == 'symbol'


@pytest.mark.parametrize('field', ['symbol', 'companyName', 'price', 'marketCap'])
def test_required_keys_fail_if_missing(rig, field):
    from stock_tracker.exceptions import ProviderResponseError
    row = dict(rig.minimal)
    del row[field]
    if field == 'marketCap':
        row['mktCap'] = 100  # Legacy field must not substitute for Stable key.
    rig.row(row)
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_company_profile('AAPL')
    assert caught.value.field == field


@pytest.mark.parametrize('name', [None, '', ' ', ' Fictional ', 1, False, []])
def test_required_name_strict_nonblank_text(rig, name):
    from stock_tracker.exceptions import ProviderResponseError
    rig.row(dict(rig.minimal, companyName=name))
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_company_profile('AAPL')
    assert caught.value.field == 'name'


@pytest.mark.parametrize('field', ['exchange', 'currency', 'sector', 'country'])
@pytest.mark.parametrize('value', [None, '', '   '])
def test_optional_missing_or_blank_text_remains_none(rig, field, value):
    rig.row(dict(rig.minimal, **{field: value}))
    assert getattr(rig.provider.get_company_profile('AAPL'), field) is None


@pytest.mark.parametrize('field', ['exchange', 'currency', 'sector', 'country'])
@pytest.mark.parametrize('value', [True, {}, ' nonblank '])
def test_optional_malformed_text_rejected_without_normalizing(rig, field, value):
    from stock_tracker.exceptions import ProviderResponseError
    rig.row(dict(rig.minimal, **{field: value}))
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_company_profile('AAPL')
    assert caught.value.field == field


@pytest.mark.parametrize('field', ['price', 'marketCap'])
@pytest.mark.parametrize('value', [True, False, '123.5', -1, [], {}])
def test_numeric_fields_reject_nonnumber_negative_bool(rig, field, value):
    from stock_tracker.exceptions import ProviderResponseError
    rig.row(dict(rig.minimal, **{field: value}))
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_company_profile('AAPL')
    assert caught.value.field == ('market_cap' if field == 'marketCap' else field)
    assert len(rig.requests) == 1


@pytest.mark.parametrize('field', ['price', 'marketCap'])
@pytest.mark.parametrize('literal', ['NaN', 'Infinity', '-Infinity', '-0.01'])
def test_json_nonfinite_or_negative_numbers_fail(rig, field, literal):
    from stock_tracker.exceptions import ProviderResponseError
    rig.body = ('[{"symbol":"AAPL","companyName":"Fictional","price":0,"marketCap":0,"' + field + '":' + literal + '}]').encode()
    with pytest.raises(ProviderResponseError):
        rig.provider.get_company_profile('AAPL')


@pytest.mark.parametrize('status,name,attempts', [(401, 'ProviderAuthenticationError', 1),
    (403, 'ProviderAccessError', 1), (404, 'ProviderUnavailableError', 1),
    (429, 'RateLimitError', 1), (500, 'ProviderUnavailableError', 2)])
def test_profile_preserves_common_status_categories(rig, status, name, attempts):
    import stock_tracker.exceptions as errors
    rig.status = status
    with pytest.raises(getattr(errors, name)):
        rig.provider.get_company_profile('AAPL')
    assert len(rig.requests) == attempts
