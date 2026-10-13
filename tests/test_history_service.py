"""History orchestration with fixed UTC clocks and typed provider fakes."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

NOW = datetime(2020, 3, 1, tzinfo=timezone.utc)
START, END = date(2020, 1, 2), date(2020, 1, 6)


def bar(session=START):
    from stock_tracker.providers.models import PriceBar
    return PriceBar("AAPL", session, Decimal("100"), Decimal("120"), Decimal("99"),
                    Decimal("110.0000000000000000001"), None, 0)


@pytest.fixture
def rig():
    from stock_tracker.domain import Stock
    from stock_tracker.services import HistoryService
    state = SimpleNamespace(stock=Stock("AAPL", exchange="NASDAQ"), clocks=[], calls=[], result=[bar(), bar(END)])
    def clock():
        state.clocks.append(1)
        return NOW
    def source(ordinal):
        state.calls.append(("source", ordinal))
        def history(symbol, start, end):
            state.calls.append((symbol, start, end))
            return state.result
        return SimpleNamespace(get_price_history=history)
    state.service = HistoryService(source, clock=clock)
    return state


def test_sparse_numeric_immutable_view_without_mutation(rig):
    result = rig.service.history(rig.stock, ordinal=7, start=START, end=END)
    assert result.stock is rig.stock
    assert (result.start, result.end) == (START, END)
    assert result.bars == (bar(), bar(END))
    assert result.bars[0].close == Decimal("110.0000000000000000001")
    assert result.bars[0].adjusted_close is None and result.bars[0].volume == 0
    assert rig.calls == [("source", 7), ("AAPL", START, END)]
    assert rig.clocks == [1]
    rig.result.clear()
    assert len(result.bars) == 2
    with pytest.raises(FrozenInstanceError):
        result.start = END


def test_default_range_resolved_once_and_carried_exactly(rig):
    rig.result = [bar(date(2020, 2, 29))]
    result = rig.service.history(rig.stock, ordinal=0)
    assert (result.start, result.end) == (date(2015, 2, 28), date(2020, 2, 29))
    assert rig.clocks == [1]
    assert rig.calls == [("source", 0), ("AAPL", result.start, result.end)]


@pytest.mark.parametrize("exchange", [None, "NYSE", "nasdaq", "XNAS", "N/A"])
def test_identity_before_clock_range_or_source(rig, exchange):
    from stock_tracker.domain import Stock
    from stock_tracker.exceptions import MarketDataUnavailableError
    with pytest.raises(MarketDataUnavailableError):
        rig.service.history(Stock("AAPL", exchange=exchange), ordinal=0, start=True)
    assert rig.clocks == rig.calls == []


@pytest.mark.parametrize("ordinal", [-1, True, 1.0, None, "0"])
def test_invalid_row_association_before_source_or_clock(rig, ordinal):
    from stock_tracker.exceptions import PersistenceValidationError
    with pytest.raises(PersistenceValidationError):
        rig.service.history(rig.stock, ordinal=ordinal)
    assert rig.clocks == rig.calls == []


@pytest.mark.parametrize("start,end", [(START, None), (None, END), (True, END), (NOW, END),
    ("2020-01-02", END), (END, START), (START, NOW.date()),
    (START, NOW.date() + timedelta(days=1)), (END-timedelta(days=3660), END)])
def test_invalid_request_before_source(rig, start, end):
    from stock_tracker.exceptions import HistoryRangeError
    with pytest.raises(HistoryRangeError):
        rig.service.history(rig.stock, ordinal=0, start=start, end=end)
    assert rig.calls == []


def test_explicit_preflight_validation_rechecks_clock_at_retrieval(rig):
    assert rig.service.validate_range(START, END) == (START, END)
    rig.service.history(rig.stock, ordinal=0, start=START, end=END)
    assert rig.clocks == [1, 1]
    assert rig.calls == [("source", 0), ("AAPL", START, END)]
    from stock_tracker.exceptions import HistoryRangeError
    with pytest.raises(HistoryRangeError):
        rig.service.validate_range(None, None)


def test_inclusive_maximum_and_same_day_ranges(rig):
    first = END - timedelta(days=3659)
    assert rig.service.validate_range(first, END) == (first, END)
    rig.result = [bar()]
    assert rig.service.history(rig.stock, ordinal=0, start=START, end=START).bars == (bar(),)


def test_constructor_defers_clock_and_dependency_work():
    from stock_tracker.services import HistoryService
    def denied(*args):
        pytest.fail("Constructor invoked external dependency")
    HistoryService(denied, clock=denied)


def test_normalizes_request_symbol_without_replacing_input_identity(rig):
    from stock_tracker.domain import Stock
    stock = Stock("aapl", exchange="NASDAQ")
    result = rig.service.history(stock, ordinal=0, start=START, end=END)
    assert result.stock is stock and stock.symbol == "aapl"
    assert rig.calls[-1] == ("AAPL", START, END)


def test_invalid_symbol_before_source(rig):
    from stock_tracker.domain import Stock
    from stock_tracker.exceptions import InvalidTickerError
    with pytest.raises(InvalidTickerError):
        rig.service.history(Stock("A A", exchange="NASDAQ"), ordinal=0, start=START, end=END)
    assert rig.calls == []


def test_authoritative_validation_rejects_forged_stock_subclass(rig):
    from stock_tracker.domain import DomainValidationError, Stock
    class Forged(Stock):
        def __post_init__(self):
            pass
    with pytest.raises(DomainValidationError):
        rig.service.history(Forged(" AAPL ", exchange="NASDAQ"), ordinal=0)
    assert rig.clocks == rig.calls == []


def test_authoritative_validation_rejects_forged_bar_subclass(rig):
    from stock_tracker.providers.models import PriceBar
    from stock_tracker.exceptions import ProviderResponseError
    class Forged(PriceBar):
        def __post_init__(self):
            pass
    rig.result = [Forged("AAPL", START, Decimal(1), Decimal(1), Decimal(1), Decimal("NaN"), None, 0)]
    with pytest.raises(ProviderResponseError):
        rig.service.history(rig.stock, ordinal=0, start=START, end=END)


def test_zero_raw_observations_are_numeric(rig):
    rig.result = [replace(bar(), open=Decimal(0), high=Decimal(0), low=Decimal(0), close=Decimal(0))]
    result = rig.service.history(rig.stock, ordinal=0, start=START, end=END)
    assert result.bars[0].close == Decimal(0) and result.bars[0].volume == 0


@pytest.mark.parametrize("now", [None, NOW.date(), datetime(2020, 3, 1),
    datetime(2020, 3, 1, tzinfo=timezone(timedelta(hours=1))), datetime(4, 1, 1, tzinfo=timezone.utc)])
def test_invalid_utc_clock_before_acquisition(rig, now):
    from stock_tracker.services import HistoryService
    from stock_tracker.exceptions import HistoryRangeError
    service = HistoryService(lambda ordinal: pytest.fail("Source reached"), clock=lambda: now)
    with pytest.raises(HistoryRangeError):
        service.history(rig.stock, ordinal=0)


@pytest.mark.parametrize("case", range(12))
def test_revalidates_provider_raw_results(rig, case):
    from stock_tracker.exceptions import MarketDataUnavailableError, ProviderResponseError
    forged = bar()
    object.__setattr__(forged, "close", Decimal("NaN"))
    cases = [None, (bar(),), [], [object()], [replace(bar(), symbol="MSFT")],
             [bar(START-timedelta(days=1))], [bar(END+timedelta(days=1))],
             [bar(), bar()], [bar(END), bar()], [replace(bar(), adjusted_close=Decimal(1))],
             [replace(bar(), volume=9223372036854775808)], [forged]]
    rig.result = cases[case]
    with pytest.raises(MarketDataUnavailableError if case == 2 else ProviderResponseError):
        rig.service.history(rig.stock, ordinal=0, start=START, end=END)
    assert rig.calls == [("source", 0), ("AAPL", START, END)]


@pytest.mark.parametrize("stage", ["source", "request"])
@pytest.mark.parametrize("name", ["ProviderTimeoutError", "ProviderUnavailableError", "RateLimitError",
    "HistoryCacheError", "MarketDataUnavailableError", "ProviderResponseError", "RuntimeError"])
def test_original_errors_propagate_without_retry_or_fabrication(rig, stage, name):
    from stock_tracker import exceptions
    from stock_tracker.services import HistoryService
    kind = RuntimeError if name == "RuntimeError" else getattr(exceptions, name)
    error = kind()
    calls = []
    def fail(*args):
        calls.append(stage)
        raise error
    source = fail if stage == "source" else lambda ordinal: SimpleNamespace(get_price_history=fail)
    with pytest.raises(kind) as caught:
        HistoryService(source, clock=lambda: NOW).history(rig.stock, ordinal=0, start=START, end=END)
    assert caught.value is error and calls == [stage]


def test_source_history_service_boundary_probe(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-I", str(root / "tests/history_service_probe.py"), str(root / "src")],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_service_preserves_real_cache_reuse_expiry_and_failure(monkeypatch, rig, tmp_path):
    from stock_tracker.providers import factory
    from stock_tracker.providers.transport import HttpResponse
    from stock_tracker.exceptions import ProviderUnavailableError
    from stock_tracker.services import HistoryService
    clock = [NOW]
    monkeypatch.setattr(factory, "datetime", SimpleNamespace(now=lambda tz: clock[0]))
    requests = []
    def get(self, url, *, headers, timeout_seconds):
        requests.append(url)
        if len(requests) > 1:
            raise ProviderUnavailableError()
        return HttpResponse(200, {}, b'[{"symbol":"AAPL","date":"2020-01-02","adjOpen":100,"adjHigh":120,"adjLow":99,"adjClose":110.0000000000000000001,"volume":0}]')
    monkeypatch.setattr(factory.UrllibHttpTransport, "get", get)
    service = HistoryService(lambda ordinal: factory.create_historical_market_data_provider("synthetic-history-service"),
                             clock=lambda: clock[0])
    first = service.history(rig.stock, ordinal=0, start=START, end=END)
    cache_bytes = (tmp_path / "stock_tracker.history-cache.json").read_bytes()
    second = service.history(rig.stock, ordinal=0, start=START, end=END)
    assert first == second and len(requests) == 1
    assert first.bars == (bar(),)
    assert not (tmp_path / "stock_tracker.sqlite3").exists()
    clock[0] += timedelta(hours=2)
    with pytest.raises(ProviderUnavailableError):
        service.history(rig.stock, ordinal=0, start=START, end=END)
    assert len(requests) == 2
    assert (tmp_path / "stock_tracker.history-cache.json").read_bytes() == cache_bytes
    assert b"synthetic-history-service" not in cache_bytes
