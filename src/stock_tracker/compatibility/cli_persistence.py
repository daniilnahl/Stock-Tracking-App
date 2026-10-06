"""Local CLI composition: SQLite state and existence-only legacy protection."""

from pathlib import Path

from watch_list import Watch_list
from stock_tracker.exceptions import LegacyStatePresentError, PersistenceError
from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository

from .watchlist_persistence import record_to_watchlist, watchlist_to_record


def _legacy_exists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        raise PersistenceError() from None
    return True


def load_cli_watchlist(path: Path, namespace: str, legacy: Path, runtime_key: str | None) -> Watch_list:
    record = SQLiteWatchlistRepository(path).get(namespace)
    if record is not None:
        return record_to_watchlist(record, runtime_key)
    if _legacy_exists(legacy):
        raise LegacyStatePresentError()
    return Watch_list("Watchlist")


def save_cli_watchlist(path: Path, namespace: str, legacy: Path, watchlist: Watch_list) -> None:
    candidate = watchlist_to_record(watchlist, namespace)
    repository = SQLiteWatchlistRepository(path)
    if repository.get(namespace) is None and _legacy_exists(legacy):
        raise LegacyStatePresentError()
    repository.save(candidate)


def storage_error_message(error: PersistenceError) -> str:
    if isinstance(error, LegacyStatePresentError):
        return (str(error) + " Preserve the original legacy file and follow the manual "
                "neutral-data transition in docs/PERSISTENCE.md.")
    return str(error)
