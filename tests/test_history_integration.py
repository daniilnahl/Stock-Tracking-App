"""Offline accepted history composition and facade/state boundary evidence."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import builtins
import io
import os
import pickle
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

NOW = datetime(2020, 3, 1, 12, tzinfo=timezone.utc)
START, END = date(2020, 1, 2), date(2020, 1, 6)


def bar(session=START):
    from stock_tracker.providers.models import PriceBar
    return PriceBar("AAPL", session, Decimal("100"), Decimal("120"), Decimal("99"),
                    Decimal("110.0000"), None, 0)


@pytest.fixture
def rig(monkeypatch, tmp_path):
    from stock import Stock
    from stock_tracker.compatibility import history_operations as history
    from stock_tracker.providers import factory
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(history, "utc_now", lambda: NOW)
    monkeypatch.setattr(factory, "datetime", SimpleNamespace(now=lambda tz: NOW))
    monkeypatch.setattr(factory.time, "monotonic", lambda: 1.0)
    credential = "synthetic-history-runtime"
    stock = Stock("AAPL", credential, exchange="NASDAQ", currency="EUR", current_price="120",
                  amount_owned="0.2500", cost_basis="100.0000", price_1d="12.345")
    return SimpleNamespace(stock=stock, credential=credential, path=tmp_path, calls=[], history=history, factory=factory)


def test_composition_io_free_explicit_policy_and_path_bound_once(rig, monkeypatch):
    factory = rig.factory
    from stock_tracker.providers import transport
    from stock_tracker.providers.transport import ProviderPolicy
    before = list(rig.path.iterdir())
    def denied(*args, **kwargs):
        raise AssertionError("Composition performed IO or clock access")
    with monkeypatch.context() as guard:
        guard.setattr(builtins, "open", denied)
        guard.setattr(io, "open", denied)
        guard.setattr(factory, "datetime", SimpleNamespace(now=denied))
        guard.setattr(factory.UrllibHttpTransport, "get", denied)
        guard.setattr(os, "getenv", denied)
        guard.setattr(transport.ssl, "create_default_context", denied)
        guard.setattr(transport.certifi, "where", denied)
        provider = factory.create_historical_market_data_provider(rig.credential)
    assert provider._repository._path == rig.path / "stock_tracker.history-cache.json"
    assert provider._policy.history_cache_ttl_seconds == 3600.0
    assert provider._policy.quote_cache_ttl_seconds == 0.0
    assert provider._policy.stale_cache_fallback is False
    assert provider._policy == ProviderPolicy(10.0, 2, frozenset({408, 500, 502, 503, 504}),
                                              0.5, 2.0, 30.0, False, 0.0, 3600.0, False)
    assert not hasattr(provider, "get_quote")
    assert factory.create_market_data_provider(rig.credential)._policy.history_cache_ttl_seconds == 0.0
    assert list(rig.path.iterdir()) == before


def test_real_composition_receipt_cache_reuse_and_state_nonmutation(rig, monkeypatch):
    factory = rig.factory
    from stock_tracker.providers.transport import HttpResponse
    payload = b'[{"symbol":"AAPL","date":"2020-01-02","adjOpen":100,"adjHigh":120,"adjLow":99,"adjClose":110.0000,"volume":0}]'
    def get(self, url, *, headers, timeout_seconds):
        rig.calls.append((url, headers, timeout_seconds))
        return HttpResponse(200, {}, payload)
    monkeypatch.setattr(factory.UrllibHttpTransport, "get", get)
    before = dict(rig.stock.__dict__)
    first = rig.stock.get_price_history(start=START, end=END)
    second = rig.stock.get_price_history(start=START, end=END)
    assert first == second == [bar()] and first is not second
    assert len(rig.calls) == 1
    assert "historical-price-eod/non-split-adjusted?symbol=AAPL&from=2020-01-02&to=2020-01-06" in rig.calls[0][0]
    assert rig.calls[0][1] == {"apikey": rig.credential}
    assert rig.stock.__dict__ == before
    assert rig.credential not in (rig.path / "stock_tracker.history-cache.json").read_text()
    assert rig.credential.encode() not in pickle.dumps(rig.stock)
    provider = factory.create_historical_market_data_provider(rig.credential)
    elsewhere = rig.path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert provider.get_price_history("AAPL", START, END) == [bar()]
    assert list(elsewhere.iterdir()) == [] and len(rig.calls) == 1


@pytest.mark.parametrize("exchange", [None, "N/A", "NYSE", "nasdaq", "NASDAQ "])
def test_identity_gate_precedes_clock_credentials_and_factory(rig, monkeypatch, exchange):
    from stock_tracker import exceptions as errors
    history, factory = rig.history, rig.factory
    rig.stock.exchange = exchange
    rig.stock.API_KEY = None
    def denied(*args, **kwargs):
        pytest.fail("Unsupported identity crossed gate")
    monkeypatch.setattr(history, "utc_now", denied)
    monkeypatch.setattr(factory, "create_historical_market_data_provider", denied)
    before = dict(rig.stock.__dict__)
    with pytest.raises(errors.MarketDataUnavailableError):
        rig.stock.get_price_history(start=True)
    assert rig.stock.__dict__ == before and list(rig.path.iterdir()) == []


def test_defaults_explicit_limits_and_leap_clamp():
    from stock_tracker.compatibility import history_operations as history
    from stock_tracker import exceptions as errors
    assert history.resolve_history_range(clock=lambda: NOW) == (date(2015, 2, 28), date(2020, 2, 29))
    start = END - timedelta(days=3659)
    assert history.resolve_history_range(start, END, clock=lambda: NOW) == (start, END)
    assert history.resolve_history_range(START, START, clock=lambda: NOW) == (START, START)
    with pytest.raises(errors.HistoryRangeError):
        history.resolve_history_range(clock=lambda: datetime(4, 1, 1, tzinfo=timezone.utc))


@pytest.mark.parametrize("start,end", [(START, None), (None, END), (True, END), (NOW, END),
    ("2020-01-02", END), (END, START), (START, NOW.date()), (END-timedelta(days=3660), END)])
def test_bad_range_before_factory(rig, monkeypatch, start, end):
    from stock_tracker import exceptions as errors
    factory = rig.factory
    monkeypatch.setattr(factory, "create_historical_market_data_provider", lambda key: pytest.fail("Factory reached"))
    with pytest.raises(errors.HistoryRangeError):
        rig.stock.get_price_history(start=start, end=end)


@pytest.mark.parametrize("symbol", ["", "A A", "A,B", "A\x00", True])
def test_bad_symbol_before_factory(rig, monkeypatch, symbol):
    from stock_tracker import exceptions as errors
    factory = rig.factory
    rig.stock.ticker_symbol = symbol
    monkeypatch.setattr(factory, "create_historical_market_data_provider", lambda key: pytest.fail("Factory reached"))
    with pytest.raises(errors.InvalidTickerError):
        rig.stock.get_price_history(start=START, end=END)


@pytest.mark.parametrize("case", range(10))
def test_fake_results_validated_without_state_mutation(rig, monkeypatch, case):
    from stock_tracker import exceptions as errors
    factory = rig.factory
    results = [None, (), [], [object()], [replace(bar(), symbol="MSFT")],
               [bar(END+timedelta(days=1))], [bar(), bar()], [bar(END), bar()],
               [replace(bar(), adjusted_close=Decimal(1))], [replace(bar(), volume=9223372036854775808)]]
    result = results[case]
    kind = errors.MarketDataUnavailableError if case == 2 else errors.ProviderResponseError
    monkeypatch.setattr(factory, "create_historical_market_data_provider", lambda key:
                        SimpleNamespace(get_price_history=lambda *args: result))
    before = dict(rig.stock.__dict__)
    with pytest.raises(kind):
        rig.stock.get_price_history(start=START, end=END)
    assert rig.stock.__dict__ == before


@pytest.mark.parametrize("name", ["ProviderTimeoutError", "RateLimitError", "ProviderResponseError",
    "HistoryCacheError", "ProviderUnavailableError", "ConfigurationError", "RuntimeError"])
def test_error_distinctions_passthrough_without_invalidation(rig, monkeypatch, name):
    from config import ConfigurationError
    from stock_tracker import exceptions as errors
    factory = rig.factory
    kind = {"ConfigurationError": ConfigurationError, "RuntimeError": RuntimeError}.get(name) or getattr(errors, name)
    error = kind("safe test failure") if kind in (ConfigurationError, RuntimeError) else kind()
    def create(key):
        raise error
    monkeypatch.setattr(factory, "create_historical_market_data_provider", create)
    before = dict(rig.stock.__dict__)
    with pytest.raises(kind) as caught:
        rig.stock.get_price_history(start=START, end=END)
    assert caught.value is error and rig.stock.__dict__ == before


def test_restored_runtime_key_and_missing_currency_no_refresh(rig, monkeypatch):
    from stock_tracker.compatibility.watchlist_persistence import watchlist_to_record, record_to_watchlist
    from watch_list import Watch_list
    factory = rig.factory
    record = watchlist_to_record(Watch_list("history", [rig.stock]), "menu_watchlist")
    rebound = "synthetic-history-rebound"
    stock = record_to_watchlist(record, rebound).stocks[0]
    stock.currency = None
    result = [bar()]
    def create(key):
        assert key == rebound
        return SimpleNamespace(get_price_history=lambda *args: result)
    monkeypatch.setattr(factory, "create_historical_market_data_provider", create)
    before = stock.__getstate__()
    returned = stock.get_price_history(start=START, end=END)
    returned.clear()
    assert result == [bar()] and stock.__getstate__() == before
    assert rebound.encode() not in pickle.dumps(stock)


def test_default_facade_normalizes_symbol_and_resolves_once(rig, monkeypatch):
    rig.stock.ticker_symbol = " aapl "
    clocks, calls = [], []
    monkeypatch.setattr(rig.history, "utc_now", lambda: clocks.append(1) or NOW)
    def get(symbol, start, end):
        calls.append((symbol, start, end))
        return [bar(end)]
    monkeypatch.setattr(rig.factory, "create_historical_market_data_provider", lambda key:
                        SimpleNamespace(get_price_history=get))
    assert rig.stock.get_price_history() == [bar(date(2020, 2, 29))]
    assert clocks == [1] and calls == [("AAPL", date(2015, 2, 28), date(2020, 2, 29))]


@pytest.mark.parametrize("credential", [None, "", " ", True, [], "synthetic\ninvalid"])
def test_historical_factory_rejects_credentials_before_path_or_cache(rig, monkeypatch, credential):
    from config import ConfigurationError
    monkeypatch.setattr(rig.factory.Path, "cwd", lambda: pytest.fail("Path resolved before credentials"))
    with pytest.raises(ConfigurationError):
        rig.factory.create_historical_market_data_provider(credential)


def test_source_history_integration_probe(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for mode in ("write", "read"):
        result = subprocess.run([sys.executable, "-I", str(root / "tests/history_integration_probe.py"),
                                 str(root / "src"), mode], cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert result.stdout == result.stderr == ""
