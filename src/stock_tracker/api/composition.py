"""Independent lazy API infrastructure graph over the established services."""

from datetime import datetime, timezone

from stock_tracker.exceptions import PersistenceError
from stock_tracker.services.history import HistoryService
from stock_tracker.services.watchlists import WatchlistService

from .app import create_app
from .configuration import ApiConfiguration, require_validated_configuration
from .context import ApiServices
from .errors import ApiFailure


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

    return create_app(token=configuration.token, services=ApiServices(
        watchlist=watchlist,
        history=HistoryService(historical_provider, clock=lambda: datetime.now(timezone.utc)),
        history_enabled=configuration.enable_history, history_source="fmp", history_cache_policy=True,
    ))
