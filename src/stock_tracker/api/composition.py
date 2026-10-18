"""Independent lazy API infrastructure graph over the established services."""

from datetime import datetime, timezone
from time import monotonic

from stock_tracker.exceptions import PersistenceError, RateLimitError
from stock_tracker.services.history import HistoryService
from stock_tracker.services.watchlists import WatchlistService
from stock_tracker.services.eps import UpcomingEpsService

from .app import create_app
from .configuration import ApiConfiguration, require_validated_configuration
from .context import ApiServices
from .errors import ApiFailure
from .eps_budget import EpsBudget


class _BudgetedEpsProvider:
    def __init__(self, provider, lease):
        self._provider, self._lease = provider, lease

    def get_upcoming_eps(self, symbol, **kwargs):
        try:
            return self._provider.get_upcoming_eps(symbol, **kwargs)
        except RateLimitError:
            self._lease.complete(rate_limited=True)
            raise
        finally:
            self._lease.complete()

    def __reduce_ex__(self, protocol):
        raise TypeError("Market-data providers cannot be serialized.")


class LegacyFilePresence:
    """Inspect only the configured legacy directory entry when a load needs it."""

    def __init__(self, path):
        self._path = path

    def __call__(self):
        try:
            self._path.lstat()
        except FileNotFoundError:
            return False
        except OSError:
            raise PersistenceError() from None
        return True


def create_local_app(configuration: ApiConfiguration):
    """Construct closures only; health and rejected requests acquire no IO."""
    require_validated_configuration(configuration)
    eps_budget = EpsBudget(monotonic) if configuration.enable_upcoming_eps else None

    def utc_now():
        return datetime.now(timezone.utc)

    def upcoming_eps_provider():
        lease = eps_budget.reserve()
        try:
            from config import ConfigurationError, load_finnhub_configuration
            from stock_tracker.providers.finnhub_factory import create_upcoming_eps_provider

            try:
                provider = create_upcoming_eps_provider(load_finnhub_configuration().api_key, clock=utc_now)
            except ConfigurationError:
                raise ApiFailure("provider_unavailable") from None
            return _BudgetedEpsProvider(provider, lease)
        except BaseException:
            lease.complete()
            raise

    def watchlist(namespace):
        from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository

        if namespace not in ("menu_watchlist", "daniils_stock_method"):
            raise ApiFailure("not_found")
        legacy = configuration.menu_legacy if namespace == "menu_watchlist" else configuration.evaluation_legacy
        return WatchlistService(SQLiteWatchlistRepository(configuration.database), namespace=namespace,
                                legacy_present=LegacyFilePresence(legacy))

    def historical_provider(ordinal):
        # HistoryService validates the actual saved Stock and range before
        # acquiring this port. FMP retains its existing key and cache policies.
        from config import ConfigurationError, load_configuration
        from stock_tracker.providers.factory import create_historical_market_data_provider

        try:
            return create_historical_market_data_provider(load_configuration().api_key,
                                                         cache_path=configuration.history_cache)
        except ConfigurationError:
            raise ApiFailure("provider_unavailable") from None

    return create_app(token=configuration.token, dashboard=configuration.enable_dashboard, services=ApiServices(
        watchlist=watchlist,
        history=HistoryService(historical_provider, clock=lambda: datetime.now(timezone.utc)),
        history_enabled=configuration.enable_history, history_source="fmp", history_cache_policy=True,
        upcoming_eps=UpcomingEpsService(upcoming_eps_provider, research_date=lambda: utc_now().date())
            if configuration.enable_upcoming_eps else None,
        upcoming_eps_enabled=configuration.enable_upcoming_eps,
    ))
