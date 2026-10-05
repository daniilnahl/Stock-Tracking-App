"""Synthetic Stable quote schema, official docs inspected 2026-10-04.

Source: https://site.financialmodelingprep.com/developer/docs/stable/quote
Optional currency is deliberately absent from the documented sample.
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
    state = SimpleNamespace(body=b'[{"symbol":"AAPL","price":123.123456789012345678,"exchange":"NASDAQ","timestamp":1577836800}]',
                            status=200, requests=[], receipt=datetime(2020, 1, 2, tzinfo=timezone.utc))
    def get(url, *, headers, timeout_seconds):
        state.requests.append((url, headers, timeout_seconds))
        return HttpResponse(state.status, {}, state.body)
    policy = ProviderPolicy(10.0, 2, frozenset({408, 500, 502, 503, 504}),
                            0.5, 2.0, 30.0, False, 0.0, 0.0, False)
    dummy = 'synthetic-quote-fixture'
    state.provider = FMPMarketDataProvider(api_key=dummy, transport=SimpleNamespace(get=get),
        policy=policy, clock=lambda: state.receipt, monotonic=lambda: 0.0,
        sleep=lambda delay: None, jitter=lambda upper: 0.0)
    state.row = lambda row: setattr(state, 'body', json.dumps([row]).encode())
    return state


def test_quote_precise_schema_and_single_normalized_request(rig):
    from stock_tracker.providers.models import Quote
    quote = rig.provider.get_quote('  aapl  ')
    assert isinstance(quote, Quote)
    assert quote.symbol == 'AAPL' and quote.price == Decimal('123.123456789012345678')
    assert quote.exchange == 'NASDAQ' and quote.currency is None
    assert quote.as_of == datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert quote.retrieved_at == rig.receipt and quote.as_of != quote.retrieved_at
    assert len(rig.requests) == 1
    url, headers, timeout = rig.requests[0]
    assert urlsplit(url).path == '/stable/quote' and parse_qs(urlsplit(url).query) == {'symbol': ['AAPL']}
    assert headers == {'apikey': 'synthetic-quote-fixture'} and timeout == 10.0
    assert 'synthetic-' not in url


@pytest.mark.parametrize('symbol', [None, True, 1, [], '', '  ', 'AA PL', 'AA\tPL', 'AAPL,MSFT',
                                    'AA\x00PL', 'AA\x7fPL', 'AA\x85PL'])
def test_local_invalid_symbol_never_calls_transport(rig, symbol):
    from stock_tracker.exceptions import InvalidTickerError
    with pytest.raises(InvalidTickerError):
        rig.provider.get_quote(symbol)
    assert rig.requests == []


@pytest.mark.parametrize('symbol', ['brk.b', 'brk-b', '^gspc', 'aapl&x'])
def test_symbol_punctuation_preserved_and_encoded(rig, symbol):
    rig.row({'symbol': symbol.upper(), 'price': 0})
    assert rig.provider.get_quote(symbol).symbol == symbol.upper()
    assert parse_qs(urlsplit(rig.requests[0][0]).query) == {'symbol': [symbol.upper()]}


@pytest.mark.parametrize('price,expected', [(None, None), (0, Decimal(0)), (123, Decimal(123))])
def test_missing_price_distinct_from_available_zero(rig, price, expected):
    rig.row({'symbol': 'AAPL', 'price': price})
    quote = rig.provider.get_quote('AAPL')
    assert quote.price == expected and quote.as_of is None
    assert quote.exchange is quote.currency is None


@pytest.mark.parametrize('body', [b'[]', b'{}', b'[1]', b'[{"symbol":"MSFT","price":1}]',
    b'[{"symbol":"aapl","price":1}]', b'[{"symbol":" AAPL ","price":1}]',
    b'[{"symbol":null,"price":1}]', b'[{"price":1}]', b'[{"symbol":"AAPL"}]',
    b'[{"symbol":"AAPL","price":1},{"symbol":"AAPL","price":2}]'])
def test_empty_vs_malformed_identity_required_fields_and_shape(rig, body):
    from stock_tracker.exceptions import MarketDataUnavailableError, ProviderResponseError
    rig.body = body
    with pytest.raises(MarketDataUnavailableError if body == b'[]' else ProviderResponseError):
        rig.provider.get_quote('AAPL')
    assert len(rig.requests) == 1


@pytest.mark.parametrize('price', [True, False, '1.25', 'NaN', -1, [], {}])
def test_malformed_price_fails_without_retry(rig, price):
    from stock_tracker.exceptions import ProviderResponseError
    rig.row({'symbol': 'AAPL', 'price': price})
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_quote('AAPL')
    assert caught.value.field == 'price' and len(rig.requests) == 1


@pytest.mark.parametrize('literal', ['NaN', 'Infinity', '-Infinity', '-0.001', '1e999999999999999999999999999'])
def test_nonfinite_and_negative_json_price(rig, literal):
    from stock_tracker.exceptions import ProviderResponseError
    rig.body = ('[{"symbol":"AAPL","price":' + literal + '}]').encode()
    with pytest.raises(ProviderResponseError):
        rig.provider.get_quote('AAPL')


@pytest.mark.parametrize('value,expected', [(None, None), ('', None), ('  ', None), ('NASDAQ', 'NASDAQ')])
def test_optional_text_normalization_and_unknown_fields(rig, value, expected):
    rig.row({'symbol': 'AAPL', 'price': 1, 'exchange': value, 'currency': value, 'future': {'x': 1}})
    quote = rig.provider.get_quote('AAPL')
    assert quote.exchange == quote.currency == expected


@pytest.mark.parametrize('field,value', [('exchange', 1), ('exchange', False), ('currency', []), ('currency', {}),
                                         ('exchange', ' NASDAQ '), ('currency', ' USD ')])
def test_optional_text_wrong_type_is_malformed(rig, field, value):
    from stock_tracker.exceptions import ProviderResponseError
    rig.row({'symbol': 'AAPL', 'price': 1, field: value})
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_quote('AAPL')
    assert caught.value.field == field


@pytest.mark.parametrize('literal,expected', [('null', None), ('0', datetime(1970, 1, 1, tzinfo=timezone.utc)),
    ('1577836800.0', datetime(2020, 1, 1, tzinfo=timezone.utc)),
    ('253402300799', datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc))])
def test_integral_unix_seconds_exact_and_utc(rig, literal, expected):
    rig.body = ('[{"symbol":"AAPL","price":1,"timestamp":' + literal + '}]').encode()
    assert rig.provider.get_quote('AAPL').as_of == expected


@pytest.mark.parametrize('value', [-1, 0.5, True, False, '1577836800', [], {}, 253402300800, 10**100])
def test_invalid_timestamp_is_safe_response_error(rig, value):
    from stock_tracker.exceptions import ProviderResponseError
    rig.row({'symbol': 'AAPL', 'price': 1, 'timestamp': value})
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider.get_quote('AAPL')
    assert caught.value.field == 'timestamp' and len(rig.requests) == 1


@pytest.mark.parametrize('literal', ['NaN', 'Infinity', '-Infinity', '1e1000000'])
def test_nonfinite_or_enormous_timestamp_does_not_leak_conversion_errors(rig, literal):
    from stock_tracker.exceptions import ProviderResponseError
    rig.body = ('[{"symbol":"AAPL","price":1,"timestamp":' + literal + '}]').encode()
    with pytest.raises(ProviderResponseError):
        rig.provider.get_quote('AAPL')


@pytest.mark.parametrize('status,name,attempts', [(401, 'ProviderAuthenticationError', 1),
    (403, 'ProviderAccessError', 1), (404, 'ProviderUnavailableError', 1),
    (429, 'RateLimitError', 1), (500, 'ProviderUnavailableError', 2)])
def test_quote_preserves_common_http_classifications(rig, status, name, attempts):
    import stock_tracker.exceptions as errors
    rig.status = status
    with pytest.raises(getattr(errors, name)):
        rig.provider.get_quote('AAPL')
    assert len(rig.requests) == attempts
