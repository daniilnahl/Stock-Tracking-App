"""History storage contract, isolated from holdings repositories."""

from typing import Protocol
from .history_cache import HistoryCacheEntry, HistoryCacheKey


class HistoryCacheRepository(Protocol):
    def get(self, key: HistoryCacheKey) -> HistoryCacheEntry | None: ...

    def put(self, entry: HistoryCacheEntry) -> None: ...
