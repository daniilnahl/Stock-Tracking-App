"""Offline ADR-0007 common transport/reliability contracts, not endpoint parsing."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from http.client import IncompleteRead, RemoteDisconnected
import io
import pickle
import socket
import ssl
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPSHandler

import pytest

SYNTHETIC_CREDENTIAL = 'synthetic-transport-credential'


@pytest.fixture
def policy():
    from stock_tracker.providers.transport import ProviderPolicy
    return ProviderPolicy(10.0, 2, frozenset({408, 500, 502, 503, 504}),
                          0.5, 2.0, 30.0, False, 0.0, 0.0, False)


@pytest.fixture
def rig(policy):
    from stock_tracker.providers.fmp import FMPMarketDataProvider
    from stock_tracker.providers.transport import HttpResponse
    state = SimpleNamespace(elapsed=0.0, delays=[], requests=[], actions=[],
                            stamp=datetime(2020, 1, 1, tzinfo=timezone.utc))

    def get(url, *, headers, timeout_seconds):
        state.requests.append((url, dict(headers), timeout_seconds))
        action = state.actions.pop(0) if state.actions else HttpResponse(200, {}, b'[]')
        if callable(action):
            action = action()
        if isinstance(action, BaseException):
            raise action
        return action

    def sleep(delay):
        state.delays.append(delay)
        state.elapsed += delay

    state.provider = FMPMarketDataProvider(
        api_key=SYNTHETIC_CREDENTIAL, transport=SimpleNamespace(get=get), policy=policy,
        clock=lambda: state.stamp, monotonic=lambda: state.elapsed,
        sleep=sleep, jitter=lambda upper: upper,
    )
    return state


@pytest.mark.parametrize('field,value', [
    ('timeout_seconds', None), ('timeout_seconds', 'secret-invalid'),
    ('timeout_seconds', 1), ('timeout_seconds', True), ('timeout_seconds', 0.0),
    ('retry_budget_seconds', float('nan')), ('backoff_base_seconds', -1.0),
    ('backoff_cap_seconds', 0.1), ('quote_cache_ttl_seconds', float('inf')),
    ('history_cache_ttl_seconds', []), ('max_attempts', True), ('max_attempts', 0),
    ('retryable_statuses', {500}), ('retryable_statuses', frozenset({429})),
    ('retryable_statuses', frozenset({True})), ('retry_on_429', True),
    ('stale_cache_fallback', 1),
])
def test_policy_rejects_invalid_invariants_safely(policy, field, value):
    with pytest.raises(ValueError) as caught:
        replace(policy, **{field: value})
    assert 'secret-invalid' not in str(caught.value)


def test_policy_explicit_values_and_frozen_invariants(policy):
    from dataclasses import FrozenInstanceError
    assert replace(policy, timeout_seconds=1.0, max_attempts=1, retryable_statuses=frozenset(),
                   backoff_base_seconds=0.0, quote_cache_ttl_seconds=2.0)
    with pytest.raises(FrozenInstanceError):
        policy.timeout_seconds = 1.0


def test_response_snapshots_headers_and_hides_body():
    from stock_tracker.providers.transport import HttpResponse
    headers = {'apikey': 'synthetic-header-value'}
    response = HttpResponse(200, headers, b'synthetic-body-value')
    headers.clear()
    assert response.headers['apikey'] == 'synthetic-header-value'
    with pytest.raises(TypeError):
        response.headers['x'] = 'y'
    assert 'synthetic-' not in repr(response)


@pytest.mark.parametrize('status,headers,body', [
    (True, {}, b''), (99, {}, b''), (600, {}, b''), (200, [], b''),
    (200, {'x': 1}, b''), (200, {}, 'raw-secret'),
])
def test_response_rejects_invalid_boundary_types(status, headers, body):
    from stock_tracker.providers.transport import HttpResponse
    from stock_tracker.exceptions import ProviderResponseError
    with pytest.raises(ProviderResponseError):
        HttpResponse(status, headers, body)


@pytest.mark.parametrize('key', [None, True, '', '  ', 'synthetic\nkey', 'synthetic\x00key', 'clé'])
def test_invalid_credentials_rejected_without_io(policy, key):
    from config import ConfigurationError
    from stock_tracker.providers.fmp import FMPMarketDataProvider
    def denied(*args):
        pytest.fail('constructor performed IO/clock work')
    with pytest.raises(ConfigurationError):
        FMPMarketDataProvider(api_key=key, transport=SimpleNamespace(get=denied), policy=policy,
                              clock=denied, monotonic=denied, sleep=denied, jitter=denied)


def test_precise_json_receipt_and_header_encoding(rig):
    from stock_tracker.providers.transport import HttpResponse
    rig.actions = [HttpResponse(200, {}, b'[{"price":1.234567890123456789,"volume":12345678901234567890}]')]
    rows, stamp = rig.provider._request_json('search-symbol', {'query': 'ABC&/ +', 'limit': '100'})
    assert rows == [{'price': Decimal('1.234567890123456789'), 'volume': 12345678901234567890}]
    assert stamp == rig.stamp
    url, headers, timeout = rig.requests[0]
    assert parse_qs(urlsplit(url).query) == {'query': ['ABC&/ +'], 'limit': ['100']}
    assert headers == {'apikey': 'synthetic-transport-credential'} and timeout == 10.0
    assert 'credential' not in url


@pytest.mark.parametrize('body', [b'\xff', b'{', b'{"error":"synthetic-secret"}', b'[1]',
    b'[NaN]', b'[Infinity]', b'[-Infinity]', b'[' + b'9' * 4400 + b']',
    b'[{"price":1e999999999999999999999999999999999999}]'])
def test_malformed_json_and_numeric_overflow_safe_without_retry(rig, body):
    from stock_tracker.providers.transport import HttpResponse
    from stock_tracker.exceptions import ProviderResponseError
    rig.actions = [HttpResponse(200, {}, body)]
    with pytest.raises(ProviderResponseError) as caught:
        rig.provider._request_json('quote', {'symbol': 'AAPL'})
    assert caught.value.__suppress_context__ or caught.value.__context__ is None
    assert 'synthetic-secret' not in str(caught.value)
    assert len(rig.requests) == 1 and rig.delays == []


@pytest.mark.parametrize('status,name', [(401, 'ProviderAuthenticationError'), (402, 'ProviderAccessError'),
    (403, 'ProviderAccessError'), (400, 'ProviderRequestError'), (422, 'ProviderRequestError'),
    (404, 'ProviderUnavailableError'), (302, 'ProviderUnavailableError'), (501, 'ProviderUnavailableError')])
def test_status_classification_no_retry(rig, status, name):
    import stock_tracker.exceptions as errors
    from stock_tracker.providers.transport import HttpResponse
    rig.actions = [HttpResponse(status, {}, b'synthetic-private-body')]
    with pytest.raises(getattr(errors, name)):
        rig.provider._request_json('profile', {'symbol': 'AAPL'})
    assert len(rig.requests) == 1 and not rig.delays


@pytest.mark.parametrize('status', [408, 500, 502, 503, 504])
def test_approved_status_retries_once_and_exhausts(rig, status):
    from stock_tracker.exceptions import ProviderUnavailableError
    from stock_tracker.providers.transport import HttpResponse
    rig.actions = [HttpResponse(status, {}, b'')] * 2
    with pytest.raises(ProviderUnavailableError):
        rig.provider._request_json('quote', {})
    assert len(rig.requests) == 2 and rig.delays == [0.5]


@pytest.mark.parametrize('timeout,retryable', [(True, True), (False, True), (False, False)])
def test_connection_failure_and_timeout_attempt_bounds(rig, timeout, retryable):
    from stock_tracker.exceptions import ProviderTimeoutError, ProviderUnavailableError
    from stock_tracker.providers.transport import _TransportTimeout, _TransportConnectionError
    error = _TransportTimeout() if timeout else _TransportConnectionError(retryable=retryable)
    rig.actions = [error, error]
    with pytest.raises(ProviderTimeoutError if timeout else ProviderUnavailableError):
        rig.provider._request_json('quote', {})
    assert len(rig.requests) == (2 if retryable else 1)
    assert rig.delays == ([0.5] if retryable else [])


def test_transient_recovers_with_remaining_timeout(rig):
    from stock_tracker.providers.transport import _TransportTimeout
    def fail():
        rig.elapsed = 22.0
        return _TransportTimeout()
    rig.actions = [fail]
    assert rig.provider._request_json('quote', {})[0] == []
    assert [call[2] for call in rig.requests] == [10.0, 7.5]
    assert rig.delays == [0.5]


@pytest.mark.parametrize('elapsed', [30.0, 29.5, 31.0])
def test_budget_denies_sleep_and_retry(rig, elapsed):
    from stock_tracker.providers.transport import _TransportTimeout
    from stock_tracker.exceptions import ProviderTimeoutError
    def fail():
        rig.elapsed = elapsed
        return _TransportTimeout()
    rig.actions = [fail]
    with pytest.raises(ProviderTimeoutError):
        rig.provider._request_json('quote', {})
    assert len(rig.requests) == 1 and rig.delays == []


def test_sleep_overshoot_rechecks_admission(rig):
    from stock_tracker.providers.transport import _TransportTimeout
    from stock_tracker.exceptions import ProviderTimeoutError
    rig.actions = [_TransportTimeout()]
    rig.provider._sleep = lambda delay: setattr(rig, 'elapsed', 31.0)
    with pytest.raises(ProviderTimeoutError):
        rig.provider._request_json('quote', {})
    assert len(rig.requests) == 1


def test_jitter_time_rechecks_budget_before_sleep(rig):
    from stock_tracker.providers.transport import _TransportTimeout
    from stock_tracker.exceptions import ProviderTimeoutError
    rig.actions = [_TransportTimeout()]
    def jitter(upper):
        rig.elapsed = 31.0
        return 0.0
    rig.provider._jitter = jitter
    with pytest.raises(ProviderTimeoutError):
        rig.provider._request_json('quote', {})
    assert len(rig.requests) == 1 and rig.delays == []


@pytest.mark.parametrize('header,expected', [(None, None), ('7', 7.0), ('-1', None), ('0.5', None),
    ('nonsense', None), ('9' * 4400, None), ('１２', None),
    ('Wed, 01 Jan 2020 00:00:08 GMT', 8.0), ('Tue, 31 Dec 2019 23:59:59 GMT', 0.0)])
def test_429_fail_fast_retry_after(rig, header, expected):
    from stock_tracker.exceptions import RateLimitError
    from stock_tracker.providers.transport import HttpResponse
    rig.actions = [HttpResponse(429, {} if header is None else {'rEtRy-AfTeR': header}, b'')]
    with pytest.raises(RateLimitError) as caught:
        rig.provider._request_json('quote', {})
    assert caught.value.retry_after_seconds == expected
    assert len(rig.requests) == 1 and rig.delays == []


@pytest.mark.parametrize('status', [200, 429])
def test_invalid_clock_propagates_programming_error(rig, status):
    from stock_tracker.providers.transport import HttpResponse
    rig.stamp = datetime(2020, 1, 1)
    rig.actions = [HttpResponse(status, {'Retry-After': 'Wed, 01 Jan 2020 00:00:08 GMT'}, b'[]')]
    with pytest.raises(ValueError, match='aware UTC'):
        rig.provider._request_json('quote', {})


@pytest.mark.parametrize('delay', [True, -1, 1, float('inf'), float('nan'), None])
def test_invalid_jitter_propagates_contract_error(rig, delay):
    from stock_tracker.providers.transport import _TransportTimeout
    rig.actions = [_TransportTimeout()]
    rig.provider._jitter = lambda upper: delay
    with pytest.raises(ValueError, match='jitter'):
        rig.provider._request_json('quote', {})


def test_unexpected_errors_propagate_and_diagnostics_are_sanitized(rig, caplog):
    from stock_tracker.exceptions import ProviderUnavailableError
    from stock_tracker.providers.transport import HttpResponse
    rig.actions = [HttpResponse(500, {'private': 'synthetic-private'}, b'synthetic-private')] * 2
    with pytest.raises(ProviderUnavailableError) as caught:
        rig.provider._request_json('quote', {'symbol': 'synthetic-private'})
    assert 'synthetic-' not in caplog.text + repr(caught.value) + repr(rig.provider)
    assert all(record.exc_info is None for record in caplog.records)
    with pytest.raises(TypeError, match='cannot be serialized'):
        pickle.dumps(rig.provider)
    rig.actions = [RuntimeError('programming')]
    with pytest.raises(RuntimeError, match='programming'):
        rig.provider._request_json('quote', {})


@pytest.mark.parametrize('operation,params', [('https://evil', {}), ('quote', {'apikey': 'synthetic-secret'}),
    ('quote', {'symbol': None}), ('quote', [])])
def test_request_route_and_parameter_validation(rig, operation, params):
    from stock_tracker.exceptions import ProviderRequestError
    with pytest.raises(ProviderRequestError):
        rig.provider._request_json(operation, params)
    assert rig.requests == []


@pytest.fixture
def urllib_boundary(monkeypatch):
    import stock_tracker.providers.transport as module
    state = SimpleNamespace(requests=[], handlers=[], action=None)
    def open_request(request, timeout):
        state.requests.append((request, timeout))
        if isinstance(state.action, BaseException):
            raise state.action
        return state.action
    def build(*handlers):
        state.handlers.extend(handlers)
        return SimpleNamespace(open=open_request)
    def tls_context(**kwargs):
        assert kwargs == {'cafile': 'synthetic-ca-path'}
        state.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return state.context
    monkeypatch.setattr(module.ssl, 'create_default_context', tls_context)
    monkeypatch.setattr(module.certifi, 'where', lambda: 'synthetic-ca-path')
    monkeypatch.setattr(module, 'build_opener', build)
    state.transport = module.UrllibHttpTransport()
    state.get = lambda: state.transport.get('https://financialmodelingprep.com/stable/quote?symbol=AAPL',
                                           headers={'apikey': 'synthetic-header'}, timeout_seconds=10.0)
    return state


@pytest.mark.parametrize('http_error', [False, True])
def test_urllib_closes_success_and_http_error_and_rejects_redirect(urllib_boundary, http_error):
    from stock_tracker.providers.transport import _RejectRedirect
    response = io.BytesIO(b'[]')
    response.status, response.headers = 200, {'x': 'y'}
    urllib_boundary.action = HTTPError('https://private', 429, 'private', {'x': 'y'}, response) if http_error else response
    result = urllib_boundary.get()
    assert result.status == (429 if http_error else 200) and result.body == b'[]' and response.closed
    handler = next(item for item in urllib_boundary.handlers if isinstance(item, _RejectRedirect))
    https = next(item for item in urllib_boundary.handlers if isinstance(item, HTTPSHandler))
    assert https._context is urllib_boundary.context
    assert https._context.check_hostname and https._context.verify_mode == ssl.CERT_REQUIRED
    assert handler.redirect_request(None, None, 302, None, None, 'https://evil') is None
    request, timeout = urllib_boundary.requests[0]
    assert request.get_method() == 'GET' and request.get_header('Apikey') == 'synthetic-header' and timeout == 10.0


@pytest.mark.parametrize('kind', ['timeout', 'reset', 'temporary-dns', 'permanent-dns', 'tls', 'protocol', 'disconnect'])
def test_urllib_maps_only_transient_failures(urllib_boundary, kind):
    from stock_tracker.providers.transport import _TransportTimeout, _TransportConnectionError
    reasons = {'timeout': TimeoutError('synthetic-private'), 'reset': ConnectionResetError('synthetic-private'),
               'temporary-dns': socket.gaierror(socket.EAI_AGAIN, 'synthetic-private'),
               'permanent-dns': socket.gaierror(socket.EAI_NONAME, 'synthetic-private'),
               'tls': ssl.SSLCertVerificationError('synthetic-private'),
               'protocol': IncompleteRead(b'synthetic-private'), 'disconnect': RemoteDisconnected('synthetic-private')}
    urllib_boundary.action = URLError(reasons[kind]) if kind not in {'protocol', 'disconnect'} else reasons[kind]
    with pytest.raises(_TransportTimeout if kind == 'timeout' else _TransportConnectionError) as caught:
        urllib_boundary.get()
    assert 'synthetic-private' not in str(caught.value) and caught.value.__suppress_context__
    if kind != 'timeout':
        assert caught.value.retryable == (kind in {'reset', 'temporary-dns', 'disconnect'})


def test_urllib_closes_failed_body_read(urllib_boundary):
    from stock_tracker.providers.transport import _TransportConnectionError
    class BrokenBody(io.BytesIO):
        status, headers = 200, {}
        def read(self):
            raise IncompleteRead(b'synthetic-private-partial')
    response = BrokenBody()
    urllib_boundary.action = response
    with pytest.raises(_TransportConnectionError) as caught:
        urllib_boundary.get()
    assert response.closed and not caught.value.retryable
    assert 'partial' not in str(caught.value) and caught.value.__suppress_context__


def test_construction_defers_tls_and_all_injected_work(monkeypatch, policy):
    import stock_tracker.providers.transport as transport
    from stock_tracker.providers.fmp import FMPMarketDataProvider
    def denied(*args, **kwargs):
        pytest.fail('construction performed IO')
    monkeypatch.setattr(transport.ssl, 'create_default_context', denied)
    monkeypatch.setattr(transport.certifi, 'where', denied)
    monkeypatch.setattr(transport, 'build_opener', denied)
    FMPMarketDataProvider(api_key=SYNTHETIC_CREDENTIAL, transport=transport.UrllibHttpTransport(), policy=policy,
                          clock=denied, monotonic=denied, sleep=denied, jitter=denied)


@pytest.mark.parametrize('url,headers,timeout', [
    ('http://financialmodelingprep.com/stable/quote', {}, 10.0),
    ('https://evil/stable/quote', {}, 10.0),
    ('https://user:private@financialmodelingprep.com/stable/quote', {}, 10.0),
    ('https://financialmodelingprep.com:444/stable/quote', {}, 10.0),
    ('https://financialmodelingprep.com/stable/quote#private', {}, 10.0),
    ('https://financialmodelingprep.com/api/v3/quote', {}, 10.0),
    ('https://financialmodelingprep.com/stable/quote', {'apikey': 'private\nheader'}, 10.0),
    ('https://financialmodelingprep.com/stable/quote', {}, float('nan')),
])
def test_urllib_rejects_unsafe_request_before_io(urllib_boundary, url, headers, timeout):
    from stock_tracker.exceptions import ProviderRequestError
    with pytest.raises(ProviderRequestError):
        urllib_boundary.transport.get(url, headers=headers, timeout_seconds=timeout)
    assert urllib_boundary.requests == urllib_boundary.handlers == []


@pytest.mark.parametrize('value', [True, None, float('inf'), float('nan')])
def test_invalid_monotonic_contract_propagates(rig, value):
    rig.provider._monotonic = lambda: value
    with pytest.raises(ValueError, match='monotonic'):
        rig.provider._request_json('quote', {})
    assert rig.requests == []


def test_backwards_monotonic_contract_propagates(rig):
    ticks = iter([0.0, -1.0])
    rig.provider._monotonic = lambda: next(ticks)
    with pytest.raises(ValueError, match='monotonic'):
        rig.provider._request_json('quote', {})
    assert rig.requests == []
