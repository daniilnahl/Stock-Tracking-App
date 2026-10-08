"""Separate-process offline cache reuse, for source and installed wheel."""

import sys
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import socket
import urllib.request
import pickle

sys.path.insert(0, sys.argv[1])
if Path(sys.argv[1]).name == "src" and (Path(sys.argv[1]).parent / "config.py").is_file():
    sys.path.insert(1, str(Path(sys.argv[1]).parent))


def denied(*args, **kwargs):
    raise AssertionError("External IO denied")


with ExitStack() as guards:
    for target, attribute in (
        (socket, "create_connection"),
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket.socket, "sendto"),
        (socket, "getaddrinfo"),
        (urllib.request, "urlopen"),
        (urllib.request.OpenerDirector, "open"),
        (pickle, "load"),
        (pickle, "loads"),
        (pickle, "dump"),
        (pickle, "dumps"),
    ):
        guards.enter_context(patch.object(target, attribute, denied))
        try:
            getattr(target, attribute)()
        except AssertionError as error:
            assert str(error) == "External IO denied"
        else:
            raise AssertionError("Guard did not reject external IO")
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from stock_tracker.persistence.history_cache import JsonHistoryCacheRepository
    from stock_tracker.providers.history_cache import CachedHistoricalMarketDataProvider
    from stock_tracker.providers.models import PriceBar, HistoryObservation
    from stock_tracker.providers.transport import ProviderPolicy

    now = datetime(2020, 1, 7, 12, tzinfo=timezone.utc)
    start, end = date(2020, 1, 2), date(2020, 1, 6)
    expected = PriceBar(
        "AAPL",
        start,
        Decimal("100.123456789012345678901234567890"),
        Decimal("120"),
        Decimal("99"),
        Decimal("110.0000"),
        None,
        0,
    )
    calls = []

    def loader(symbol, first, last):
        calls.append((symbol, first, last))
        if sys.argv[3] == "read":
            raise AssertionError("Fresh cache must suppress retrieval across processes")
        return HistoryObservation((expected,), now)

    repository = JsonHistoryCacheRepository(Path(sys.argv[2]), lambda: now)
    policy = ProviderPolicy(
        10.0,
        2,
        frozenset({408, 500, 502, 503, 504}),
        0.5,
        2.0,
        30.0,
        False,
        0.0,
        3600.0,
        False,
    )
    adapter = CachedHistoricalMarketDataProvider(
        repository=repository, loader=loader, clock=lambda: now, policy=policy
    )
    assert adapter.get_price_history(" aapl ", start, end) == [expected]
    assert len(calls) == (1 if sys.argv[3] == "write" else 0)
    assert str(adapter.get_price_history("AAPL", start, end)[0].close) == "110.0000"
    for name in (
        "stock_tracker.persistence.history_cache",
        "stock_tracker.persistence.history_protocols",
        "stock_tracker.providers.history_cache",
    ):
        assert (
            Path(sys.modules[name].__file__)
            .resolve()
            .is_relative_to(Path(sys.argv[1]).resolve())
        )
    import config
    expected_root = Path(sys.argv[1]).parent if Path(sys.argv[1]).name == "src" else Path(sys.argv[1])
    assert Path(config.__file__).resolve() == (expected_root / "config.py").resolve()
    assert Path(sys.modules["stock_tracker.providers.fmp"].__file__).resolve() == (
        Path(sys.argv[1]) / "stock_tracker" / "providers" / "fmp.py").resolve()
