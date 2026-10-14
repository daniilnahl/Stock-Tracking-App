"""Explicit shared services and admission for later bounded data routes."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

from stock_tracker.services.history import HistoryService
from stock_tracker.services.watchlists import WatchlistService

from .errors import ApiFailure
from .json_response import BoundedJSONResponse


@dataclass(frozen=True, slots=True)
class ApiServices:
    """Ports supplied by callers; no provider/repository construction here."""

    watchlist: Callable[[str], WatchlistService] | None = None
    history: HistoryService | None = None
    history_enabled: bool = False
    history_source: str | None = None
    history_cache_policy: bool = False

    def __post_init__(self):
        if self.watchlist is not None and not callable(self.watchlist):
            raise ValueError("Invalid API service dependencies.")
        if self.history_source not in (None, "fmp") or (
            type(self.history_enabled) is not bool or type(self.history_cache_policy) is not bool
        ):
            raise ValueError("Invalid API service dependencies.")
        if self.history_cache_policy and self.history_source != "fmp":
            raise ValueError("Invalid API provenance declaration.")


class Admission:
    def __init__(self):
        self._lock = Lock()
        self._active = 0
        self._history = 0

    def reserve(self, history: bool):
        with self._lock:
            if self._active >= 4 or (history and self._history >= 1):
                raise ApiFailure("api_busy")
            self._active += 1
            self._history += int(history)

    def release(self, history: bool):
        with self._lock:
            self._active -= 1
            self._history -= int(history)


async def run_data_operation(app, operation: Callable[[], object], *, history: bool = False):
    """Admit before acquiring dependencies; hold until actual worker termination.

    Later handlers supply a closure that acquires a service, invokes it, and
    returns the explicitly serialized neutral payload. No data route exists here.
    """
    if type(history) is not bool or not callable(operation):
        raise ApiFailure("internal_error")
    admission = app.state.api_admission
    admission.reserve(history)
    ownership = Lock()
    started, released = False, False

    def release_before_start():
        nonlocal released
        with ownership:
            if not started and not released:
                released = True
                admission.release(history)

    def execute():
        nonlocal started, released
        with ownership:
            if released:
                # A canceled queued worker can never acquire dependencies later.
                return None
            started = True
        try:
            return BoundedJSONResponse(operation())
        finally:
            with ownership:
                if not released:
                    released = True
                    admission.release(history)

    try:
        worker = asyncio.create_task(asyncio.to_thread(execute))
    except BaseException:
        release_before_start()
        raise
    # A canceled/disconnected caller cannot cancel the worker or release its
    # slot prematurely. Retrieve failures even if the caller has disappeared,
    # preventing an unattended task traceback containing private values.
    def completed(task):
        release_before_start()
        if not task.cancelled():
            task.exception()

    worker.add_done_callback(completed)
    return await asyncio.shield(worker)
