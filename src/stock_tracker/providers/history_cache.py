"""Historical-only capability decorator with explicit receipt and freshness."""

from collections.abc import Callable
from datetime import date, datetime
import logging

from stock_tracker.exceptions import (
    HistoryCacheError,
    HistoryRangeError,
    ProviderResponseError,
)
from stock_tracker.persistence.history_cache import (
    HistoryCacheEntry,
    HistoryCacheKey,
    cache_admissible,
)
from stock_tracker.persistence.history_protocols import HistoryCacheRepository
from .fmp import _input_symbol, _utc
from .models import HistoryObservation, PriceBar
from .transport import ProviderPolicy

logger = logging.getLogger(__name__)


class CachedHistoricalMarketDataProvider:
    """Fresh exact-request reuse; no quote capability or stale fallback."""

    def __init__(
        self,
        *,
        repository: HistoryCacheRepository,
        loader: Callable[[str, date, date], HistoryObservation],
        clock: Callable[[], datetime],
        policy: ProviderPolicy,
    ):
        if (
            not isinstance(policy, ProviderPolicy)
            or not callable(loader)
            or not callable(clock)
        ):
            raise ValueError("History decorator requires policy, loader and clock.")
        self._repository, self._loader, self._clock, self._policy = (
            repository,
            loader,
            clock,
            policy,
        )

    def get_price_history(self, symbol: str, start: date, end: date) -> list[PriceBar]:
        requested = _input_symbol(symbol)
        if (
            type(start) is not date
            or type(end) is not date
            or start > end
            or (end - start).days >= 3660
        ):
            raise HistoryRangeError()
        now = _utc(self._clock)
        if end >= now.date():
            raise HistoryRangeError()
        key = HistoryCacheKey("fmp", "raw-eod-v1", requested, start, end, "raw")
        ttl = self._policy.history_cache_ttl_seconds
        if ttl:
            cached = self._repository.get(key)
            if cached is not None:
                if not isinstance(cached, HistoryCacheEntry):
                    raise HistoryCacheError()
                cached.__post_init__()
                if cached.key.symbol != requested:
                    raise ProviderResponseError(field="symbol")
                if cached.key != key:
                    raise ProviderResponseError(field="date")
                if 0 <= (now - cached.retrieved_at).total_seconds() < ttl:
                    return list(cached.bars)
        observed = self._loader(requested, start, end)
        if not isinstance(observed, HistoryObservation):
            raise ProviderResponseError()
        observed.__post_init__()
        for bar in observed.bars:
            bar.__post_init__()
            if bar.symbol != requested:
                raise ProviderResponseError(field="symbol")
            if not start <= bar.date <= end:
                raise ProviderResponseError(field="date")
        if ttl:
            entry = HistoryCacheEntry(key, observed.retrieved_at, observed.bars)
            if cache_admissible(entry):
                self._repository.put(entry)
            else:
                logger.debug("Historical cache admission bypass: resource limit.")
        return list(observed.bars)
