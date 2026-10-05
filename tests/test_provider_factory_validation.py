"""Accepted production composition and legacy bool wrapper without CSV IO."""

from datetime import datetime, timezone
import builtins
import io
import pickle
from types import SimpleNamespace

import pytest


def test_factory_explicit_policy_io_free_and_no_environment_or_key_serialization(monkeypatch):
    from stock_tracker.providers import factory
    from stock_tracker.providers.transport import ProviderPolicy
    import os
    def denied(*args, **kwargs):
        pytest.fail('factory performed environment/IO/clock work')
    monkeypatch.setattr(os, 'getenv', denied)
    monkeypatch.setattr(factory.time, 'monotonic', denied)
    monkeypatch.setattr(factory.time, 'sleep', denied)
    monkeypatch.setattr(factory.random, 'uniform', denied)
    monkeypatch.setattr(factory, 'datetime', SimpleNamespace(now=denied))
    monkeypatch.setattr(factory.UrllibHttpTransport, 'get', denied)
    import stock_tracker.providers.transport as transport
    monkeypatch.setattr(transport.ssl, 'create_default_context', denied)
    monkeypatch.setattr(transport.certifi, 'where', denied)
    dummy = 'synthetic-factory-fixture'
    first = factory.create_market_data_provider(dummy)
    second = factory.create_market_data_provider(dummy)
    assert first is not second and first._transport is not second._transport
    assert first._policy == ProviderPolicy(10.0, 2, frozenset({408, 500, 502, 503, 504}),
                                           0.5, 2.0, 30.0, False, 0.0, 0.0, False)
    assert all(callable(getattr(first, name)) for name in
               ('resolve_symbol', 'get_quote', 'get_company_profile', 'get_period_changes'))
    assert dummy not in repr(first)
    with pytest.raises(TypeError, match='cannot be serialized'):
        pickle.dumps(first)


def test_factory_clock_sleep_monotonic_and_full_jitter_injections(monkeypatch):
    from stock_tracker.providers import factory
    stamp = datetime(2020, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(factory, 'datetime', SimpleNamespace(now=lambda tz: stamp if tz is timezone.utc else None))
    monkeypatch.setattr(factory.time, 'monotonic', lambda: 123.0)
    delays = []
    monkeypatch.setattr(factory.time, 'sleep', delays.append)
    ranges = []
    monkeypatch.setattr(factory.random, 'uniform', lambda low, high: ranges.append((low, high)) or 0.2)
    dummy = 'synthetic-factory-fixture'
    provider = factory.create_market_data_provider(dummy)
    assert provider._clock() == stamp and provider._monotonic() == 123.0
    provider._sleep(0.2)
    assert delays == [0.2] and provider._jitter(0.5) == 0.2 and ranges == [(0.0, 0.5)]


@pytest.mark.parametrize('key', [None, '', ' ', True, [], 'synthetic\ninvalid'])
def test_factory_missing_or_invalid_credentials_safe_no_request(key):
    from stock_tracker.providers.factory import create_market_data_provider
    from config import ConfigurationError
    with pytest.raises(ConfigurationError) as caught:
        create_market_data_provider(key)
    assert 'synthetic' not in str(caught.value)


@pytest.mark.parametrize('csv_state', ['present', 'missing', 'malformed', 'unreadable'])
@pytest.mark.parametrize('outcome', ['success', 'invalid', 'inconclusive', 'unavailable', 'timeout', 'rate', 'auth', 'malformed', 'programming'])
def test_wrapper_preserves_csv_and_propagates_all_failures(monkeypatch, tmp_path, csv_state, outcome):
    import stock_tracker.exceptions as errors
    from stock_tracker.providers.models import InstrumentIdentity
    from utils import utility_module as utility
    path = tmp_path / 'list_of_valid_tickers.csv'
    before = None
    if csv_state == 'unreadable':
        path.mkdir()  # Opening as CSV would fail; wrapper must never try.
    elif csv_state != 'missing':
        before = b'AAPL\n' if csv_state == 'present' else b'\xff,broken\n'
        path.write_bytes(before)
    def denied(*args, **kwargs):
        pytest.fail('validation attempted CSV or generic legacy transport')
    monkeypatch.setattr(utility, 'read_file', denied)
    monkeypatch.setattr(utility, 'write_file', denied)
    monkeypatch.setattr(utility, 'get_jsonparsed_data', denied)
    kinds = {'invalid': errors.InvalidTickerError, 'inconclusive': errors.InstrumentLookupInconclusiveError,
             'unavailable': errors.ProviderUnavailableError, 'timeout': errors.ProviderTimeoutError,
             'rate': errors.RateLimitError, 'auth': errors.ProviderAuthenticationError,
             'malformed': errors.ProviderResponseError, 'programming': RuntimeError}
    calls = []
    def resolve(symbol):
        calls.append(symbol)
        if outcome != 'success':
            raise kinds[outcome]()
        return InstrumentIdentity(symbol, 'NASDAQ', None, None)
    def factory(key):
        assert key == 'synthetic-wrapper-fixture'
        return SimpleNamespace(resolve_symbol=resolve)
    monkeypatch.setattr(utility.provider_factory, 'create_market_data_provider', factory)
    with monkeypatch.context() as guard:
        guard.setattr(builtins, 'open', denied)
        guard.setattr(io, 'open', denied)
        if outcome in {'success', 'invalid'}:
            assert utility.check_ticker('AAPL', 'synthetic-wrapper-fixture') is (outcome == 'success')
        else:
            with pytest.raises(kinds[outcome]):
                utility.check_ticker('AAPL', 'synthetic-wrapper-fixture')
    assert calls == ['AAPL']  # Existing CSV positives never short-circuit resolution.
    if before is not None:
        assert path.read_bytes() == before
    elif csv_state == 'missing':
        assert not path.exists()
    else:
        assert path.is_dir() and list(path.iterdir()) == []
