"""Existence-only legacy storage adapter; no legacy contents are accessed."""

from pathlib import Path

from stock_tracker.exceptions import PersistenceError, PersistenceValidationError


class LegacyFilePresence:
    """Inspect an explicit directory entry lazily without following its target."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path):
            raise PersistenceValidationError()
        self._path = path

    def __call__(self) -> bool:
        try:
            self._path.lstat()
        except FileNotFoundError:
            return False
        except OSError:
            raise PersistenceError() from None
        return True
