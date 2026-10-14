"""Lazy production dependencies and legacy object mapping outside services."""

from dataclasses import replace

from stock_tracker.compatibility import history_operations
from stock_tracker.compatibility.watchlist_persistence import record_to_watchlist, watchlist_to_record
from stock_tracker.persistence.models import WatchlistRecord
from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
from stock_tracker.providers import factory
from stock_tracker.services.current_data import CurrentDataService
from stock_tracker.services.history import HistoryService
from stock_tracker.services.watchlists import WatchlistService

from .current_data import CurrentProviderSourceAdapter
from .presentation import apply_entry_update
from .storage import LegacyFilePresence


def local_service(path, namespace, legacy):
    return WatchlistService(SQLiteWatchlistRepository(path), namespace=namespace,
                            legacy_present=LegacyFilePresence(legacy))


def current_service(watchlist, runtime_key):
    def acquire(operation, ordinal):
        key = runtime_key if ordinal is None else watchlist.stocks[ordinal].API_KEY
        return factory.create_market_data_provider(key)
    return CurrentDataService(CurrentProviderSourceAdapter(acquire))


def history_service(watchlist, cache_path):
    return HistoryService(
        lambda ordinal: factory.create_historical_market_data_provider(
            watchlist.stocks[ordinal].API_KEY, cache_path=cache_path,
        ),
        clock=lambda: history_operations.utc_now(),
    )


def publish_entry(facade, entry, namespace):
    restored = record_to_watchlist(WatchlistRecord(namespace, "Watchlist", (entry,)), facade.API_KEY).stocks[0]
    facade.__dict__.update(restored.__dict__)


def publish_update(watchlist, namespace, update):
    # Use the live projected fields, not a stale service candidate, on each stage.
    existing = watchlist_to_record(watchlist, namespace).entries[update.ordinal]
    publish_entry(watchlist.stocks[update.ordinal], apply_entry_update(existing, update), namespace)


def append_prepared(watchlist, record, runtime_key):
    added = WatchlistRecord(record.namespace, record.name, record.entries[len(watchlist.stocks):])
    watchlist.stocks.extend(record_to_watchlist(added, runtime_key).stocks)


def refresh_watchlist(watchlist, namespace, service):
    if len({id(facade) for facade in watchlist.stocks}) == len(watchlist.stocks):
        service.refresh(
            watchlist_to_record(watchlist, namespace),
            on_update=lambda update: publish_update(watchlist, namespace, update),
        )
        return
    # Repeated references observe earlier publication on the same facade. Map
    # each live occurrence to a one-row service request, rebasing its ordinal at
    # the provider/progress ports. The application still owns every fetch stage.
    for ordinal in range(len(watchlist.stocks)):
        live = watchlist_to_record(watchlist, namespace)
        row = WatchlistRecord(namespace, live.name, (live.entries[ordinal],))
        service = CurrentDataService(CurrentProviderSourceAdapter(
            lambda operation, index: factory.create_market_data_provider(watchlist.stocks[ordinal].API_KEY),
        ))
        service.refresh(row, on_update=lambda update: publish_update(
            watchlist, namespace, replace(update, ordinal=ordinal),
        ))


def remove_from_watchlist(service, watchlist, namespace, symbol):
    record = watchlist_to_record(watchlist, namespace)
    facades = {id(entry.stock): facade for entry, facade in zip(record.entries, watchlist.stocks)}
    if len({id(facade) for facade in watchlist.stocks}) == len(watchlist.stocks):
        remaining = service.remove(record, symbol)
        watchlist.stocks[:] = [facades[id(entry.stock)] for entry in remaining.entries]
    else:
        # Explicit root callers can alias one facade in several positions. The
        # legacy forward iterator removes its first identical reference, whereas
        # neutral service rows are independent occurrences. Preserve that adapter
        # behavior without inferring aliases from equal domain identities.
        aliases = list(watchlist.stocks)
        entries = {id(facade): entry for facade, entry in zip(watchlist.stocks, record.entries)}
        for facade in aliases:
            row = WatchlistRecord(namespace, record.name, (entries[id(facade)],))
            if not service.remove(row, symbol).entries:
                aliases.remove(facade)
        watchlist.stocks[:] = aliases
