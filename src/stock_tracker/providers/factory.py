"""IO-free composition of the explicitly approved ADR-0007 production profile."""

from datetime import datetime, timezone
import random
import time
from pathlib import Path

from config import ConfigurationError, require_api_key
from .fmp import FMPMarketDataProvider
from .protocols import MarketDataProvider
from .protocols import HistoricalMarketDataProvider
from .history_cache import CachedHistoricalMarketDataProvider
from stock_tracker.persistence.history_cache import JsonHistoryCacheRepository
from .transport import ProviderPolicy, UrllibHttpTransport


def create_market_data_provider(api_key: str | None) -> MarketDataProvider:
    if api_key is not None and not isinstance(api_key, str):
        raise ConfigurationError("Market-data credential must be a valid header value.")
    key = require_api_key(api_key)
    policy = ProviderPolicy(
        timeout_seconds=10.0, max_attempts=2,
        retryable_statuses=frozenset({408, 500, 502, 503, 504}),
        backoff_base_seconds=0.5, backoff_cap_seconds=2.0,
        retry_budget_seconds=30.0, retry_on_429=False,
        quote_cache_ttl_seconds=0.0, history_cache_ttl_seconds=0.0,
        stale_cache_fallback=False,
    )
    return FMPMarketDataProvider(api_key=key, transport=UrllibHttpTransport(), policy=policy,
                               clock=lambda: datetime.now(timezone.utc), monotonic=time.monotonic,
                               sleep=time.sleep, jitter=lambda upper: random.uniform(0.0, upper))


def create_historical_market_data_provider(api_key: str | None) -> HistoricalMarketDataProvider:
    """Compose the accepted historical-only capability without reading its sidecar."""
    if api_key is not None and not isinstance(api_key, str):
        raise ConfigurationError("Market-data credential must be a valid header value.")
    key = require_api_key(api_key)
    policy = ProviderPolicy(
        timeout_seconds=10.0, max_attempts=2,
        retryable_statuses=frozenset({408, 500, 502, 503, 504}),
        backoff_base_seconds=0.5, backoff_cap_seconds=2.0,
        retry_budget_seconds=30.0, retry_on_429=False,
        quote_cache_ttl_seconds=0.0, history_cache_ttl_seconds=3600.0,
        stale_cache_fallback=False,
    )
    def clock() -> datetime:
        return datetime.now(timezone.utc)
    provider = FMPMarketDataProvider(
        api_key=key, transport=UrllibHttpTransport(), policy=policy,
        clock=clock, monotonic=time.monotonic, sleep=time.sleep,
        jitter=lambda upper: random.uniform(0.0, upper),
    )
    path = Path.cwd() / "stock_tracker.history-cache.json"
    return CachedHistoricalMarketDataProvider(
        repository=JsonHistoryCacheRepository(path, clock),
        loader=provider._load_price_history, clock=clock, policy=policy,
    )
