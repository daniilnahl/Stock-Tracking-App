"""Credential acquisition adapter; service code never imports configuration."""

from collections.abc import Callable
from typing import Literal

from config import ConfigurationError
from stock_tracker.providers.protocols import MarketDataProvider


class CurrentProviderSourceAdapter:
    """Acquire the caller's runtime provider lazily, preserving configuration errors."""

    def __init__(
        self, acquire: Callable[[Literal["resolve", "profile", "periods"], int | None], MarketDataProvider],
    ) -> None:
        self._acquire = acquire

    def __call__(
        self, operation: Literal["resolve", "profile", "periods"], ordinal: int | None,
        *, on_configuration_failure: Callable[[], None] | None = None,
    ) -> MarketDataProvider:
        try:
            return self._acquire(operation, ordinal)
        except ConfigurationError:
            if on_configuration_failure is not None:
                on_configuration_failure()
            raise
