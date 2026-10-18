"""Process-local EPS attempts and leases; no sleep, persistence or refund."""

from collections import deque
from collections.abc import Callable
from math import isfinite
from threading import Lock

from .errors import ApiFailure


class EpsBudget:
    def __init__(self, monotonic: Callable[[], float]):
        if not callable(monotonic):
            raise ValueError("EPS budget requires a monotonic clock.")
        self._clock = monotonic
        self._lock = Lock()
        self._last = None
        self._failed = False
        self._attempts = deque()
        self._active = None
        with self._lock:
            self._quiet_since = self._now()

    def _now(self):
        if self._failed:
            raise ApiFailure("provider_unavailable")
        try:
            now = self._clock()
        except Exception:
            # The injected infrastructure clock may carry private diagnostics.
            self._failed = True
            raise ApiFailure("provider_unavailable") from None
        if type(now) is not float or not isfinite(now) or (self._last is not None and now < self._last):
            self._failed = True
            raise ApiFailure("provider_unavailable")
        self._last = now
        return now

    def reserve(self):
        with self._lock:
            now = self._now()
            while self._attempts and now - self._attempts[0] >= 60.0:
                self._attempts.popleft()
            if self._active is not None or now - self._quiet_since < 60.0 or len(self._attempts) >= 30:
                raise ApiFailure("eps_rate_limited")
            identity = object()
            self._active = identity
            self._attempts.append(now)
            return EpsLease(self, identity)

    def _complete(self, identity, *, rate_limited):
        with self._lock:
            if self._active is not identity:
                return
            try:
                if rate_limited:
                    self._quiet_since = self._now()
            finally:
                self._active = None


class EpsLease:
    def __init__(self, budget, identity):
        self._budget, self._identity = budget, identity

    def complete(self, *, rate_limited=False):
        self._budget._complete(self._identity, rate_limited=rate_limited)
