"""Synthetic Stable search schema, official docs inspected 2026-10-04.

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-symbol
Search completeness is not guaranteed; ADR-0008 chooses scoped product rejection.
"""

from datetime import datetime, timezone
import json
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest


@pytest.fixture
def rig():
    from stock_tracker.providers.fmp import FMPMarketDataProvider
    from stock_tracker.providers.transport import HttpResponse, ProviderPolicy
    state = SimpleNamespace(rows=[{'symbol': 'AAPL', 'exchange': 'NASDAQ'}], status=200, requests=[])
    def get(url, *, headers, timeout_seconds):
        state.requests.append((url, headers, timeout_seconds))
        return HttpResponse(state.status, {}, json.dumps(state.rows).encode())
    dummy = 'synthetic-lookup-fixture'
    state.provider = FMPMarketDataProvider(api_key=dummy, transport=SimpleNamespace(get=get),
        policy=ProviderPolicy(10.0, 2, frozenset({408, 500, 502, 503, 504}), 0.5, 2.0, 30.0, False, 0.0, 0.0, False),
        clock=lambda: datetime(2020, 1, 1, tzinfo=timezone.utc), monotonic=lambda: 0.0,
        sleep=lambda delay: None, jitter=lambda upper: 0.0)
    return state


def test_unique_exact_scoped_match_and_single_encoded_request(rig):
    from stock_tracker.providers.models import InstrumentIdentity
    rig.rows = [{'symbol': 'AAP', 'exchange': 'NASDAQ'},
                {'symbol': 'AAPL', 'exchange': 'NYSE'},
                {'symbol': 'AAPL', 'exchange': 'NASDAQ', 'name': 'Fictional company', 'currency': 'USD'}]
    assert rig.provider.resolve_symbol(' aapl ') == InstrumentIdentity('AAPL', 'NASDAQ', 'Fictional company', 'USD')
    assert len(rig.requests) == 1
    url, headers, timeout = rig.requests[0]
    assert urlsplit(url).path == '/stable/search-symbol'
    assert parse_qs(urlsplit(url).query) == {'query': ['AAPL'], 'limit': ['100'], 'exchange': ['NASDAQ']}
    assert headers == {'apikey': 'synthetic-lookup-fixture'} and timeout == 10.0
    assert 'synthetic-' not in url


@pytest.mark.parametrize('rows', [[], [{'symbol': 'AAPLX', 'exchange': 'NASDAQ'}],
    [{'symbol': 'MSFT', 'exchange': 'NASDAQ'}], [{'symbol': 'AAPL', 'exchange': 'NYSE'}],
    [{'symbol': 'AAPL', 'exchange': 'Nasdaq'}],
    [{'symbol': 'X' + str(i), 'exchange': 'NASDAQ'} for i in range(100)]])
def test_no_exact_scope_result_rejects_candidate_without_global_truth_claim(rig, rows):
    from stock_tracker.exceptions import InvalidTickerError
    rig.rows = rows
    with pytest.raises(InvalidTickerError):
        rig.provider.resolve_symbol('AAPL')
    assert len(rig.requests) == 1


@pytest.mark.parametrize('rows', [None, {}, [None], [{}], [{'symbol': 'AAPL'}],
    [{'exchange': 'NASDAQ'}], [{'symbol': True, 'exchange': 'NASDAQ'}],
    [{'symbol': 'aapl', 'exchange': 'NASDAQ'}], [{'symbol': ' AAPL ', 'exchange': 'NASDAQ'}],
    [{'symbol': 'AAPL', 'exchange': None}], [{'symbol': 'AAPL', 'exchange': ''}],
    [{'symbol': 'AAPL', 'exchange': ' NASDAQ '}], [{'symbol': 'AAPL', 'exchange': 1}],
    [{'symbol': 'AAPL', 'exchange': 'NASDAQ'}] * 2,
    [{'symbol': 'AAPL', 'exchange': 'NASDAQ'}, {'symbol': 'MSFT'}],
    [{'symbol': 'MSFT', 'exchange': 'NASDAQ'}, {'symbol': 'GOOG'}]])
def test_every_row_validated_before_exact_identity_publication(rig, rows):
    from stock_tracker.exceptions import ProviderResponseError
    rig.rows = rows
    with pytest.raises(ProviderResponseError):
        rig.provider.resolve_symbol('AAPL')
    assert len(rig.requests) == 1


@pytest.mark.parametrize('value', [None, '', '  '])
def test_optional_metadata_missing_blank_none(rig, value):
    rig.rows = [{'symbol': 'AAPL', 'exchange': 'NASDAQ', 'name': value, 'currency': value}]
    result = rig.provider.resolve_symbol('AAPL')
    assert result.name is result.currency is None


@pytest.mark.parametrize('field,value', [('name', True), ('currency', []), ('name', ' Fictional '), ('currency', ' USD ')])
def test_optional_nonblank_metadata_strict(rig, field, value):
    from stock_tracker.exceptions import ProviderResponseError
    rig.rows = [{'symbol': 'AAPL', 'exchange': 'NASDAQ', field: value}]
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.resolve_symbol('AAPL')
    assert caught.value.field == field


@pytest.mark.parametrize('symbol', [None, True, '', ' ', 'AA PL', 'AA\x00PL', 'AAPL,MSFT'])
def test_invalid_local_input_before_io(rig, symbol):
    from stock_tracker.exceptions import InvalidTickerError
    with pytest.raises(InvalidTickerError):
        rig.provider.resolve_symbol(symbol)
    assert rig.requests == []


@pytest.mark.parametrize('status,name,attempts', [(401, 'ProviderAuthenticationError', 1),
    (403, 'ProviderAccessError', 1), (404, 'ProviderUnavailableError', 1),
    (429, 'RateLimitError', 1), (500, 'ProviderUnavailableError', 2)])
def test_lookup_retains_common_failure_categories(rig, status, name, attempts):
    import stock_tracker.exceptions as errors
    rig.status = status
    with pytest.raises(getattr(errors, name)):
        rig.provider.resolve_symbol('AAPL')
    assert len(rig.requests) == attempts


def test_lookup_timeout_is_not_false_validation(rig):
    from stock_tracker.providers.transport import _TransportTimeout
    from stock_tracker.exceptions import ProviderTimeoutError
    def get(*args, **kwargs):
        raise _TransportTimeout()
    rig.provider._transport = SimpleNamespace(get=get)
    with pytest.raises(ProviderTimeoutError):
        rig.provider.resolve_symbol('AAPL')


@pytest.mark.parametrize('rows,expected', [([], False),
    ([{'symbol': 'AAPLX', 'exchange': 'NASDAQ'}], False),
    ([{'symbol': 'AAPL', 'exchange': 'NASDAQ'}], True)])
def test_real_adapter_wrapper_returns_scoped_result_without_csv(rig, rows, expected, monkeypatch, tmp_path):
    from utils import utility_module as utility
    path = tmp_path / 'list_of_valid_tickers.csv'
    path.write_bytes(b'AAPL\n')
    rig.rows = rows
    monkeypatch.setattr(utility.provider_factory, 'create_market_data_provider', lambda key: rig.provider)
    def denied(*args, **kwargs):
        pytest.fail('validation used CSV or legacy transport')
    for name in ('read_file', 'write_file', 'get_jsonparsed_data'):
        monkeypatch.setattr(utility, name, denied)
    assert utility.check_ticker(' aapl ', 'synthetic-wrapper-fixture') is expected
    assert len(rig.requests) == 1 and path.read_bytes() == b'AAPL\n'
