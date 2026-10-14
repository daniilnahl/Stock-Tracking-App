"""Local CLI composition: SQLite state and existence-only legacy protection."""

from pathlib import Path

from watch_list import Watch_list
from stock_tracker.exceptions import LegacyStatePresentError, PersistenceError
from stock_tracker.cli.storage import LegacyFilePresence
from stock_tracker.services.watchlists import WatchlistService
from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository

from .watchlist_persistence import record_to_watchlist, watchlist_to_record


def load_cli_watchlist(path: Path, namespace: str, legacy: Path, runtime_key: str | None) -> Watch_list:
    service = WatchlistService(SQLiteWatchlistRepository(path), namespace=namespace,
                               legacy_present=LegacyFilePresence(legacy))
    return record_to_watchlist(service.load(), runtime_key)


def save_cli_watchlist(path: Path, namespace: str, legacy: Path, watchlist: Watch_list) -> None:
    candidate = watchlist_to_record(watchlist, namespace)
    service = WatchlistService(SQLiteWatchlistRepository(path), namespace=namespace,
                               legacy_present=LegacyFilePresence(legacy))
    service.save(candidate)


def storage_error_message(error: PersistenceError) -> str:
    if isinstance(error, LegacyStatePresentError):
        return (str(error) + " Preserve the original legacy file and follow the manual "
                "neutral-data transition in docs/PERSISTENCE.md.")
    return str(error)
