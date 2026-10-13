"""Injected application dependency ports; concrete composition stays outside."""

from collections.abc import Callable
from typing import Literal, Protocol

from stock_tracker.providers.protocols import HistoricalMarketDataProvider, MarketDataProvider


class LegacyPresence(Protocol):
    def __call__(self) -> bool: ...


class CurrentProviderSource(Protocol):
    def __call__(
        self, operation: Literal["resolve", "profile", "periods"], ordinal: int | None,
        *, on_configuration_failure: Callable[[], None] | None = None,
    ) -> MarketDataProvider: ...


class HistoricalProviderSource(Protocol):
    def __call__(self, ordinal: int) -> HistoricalMarketDataProvider: ...
