"""Common FMP request mechanism; capability parsers are separate M2 issues."""

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
import json
import logging
from math import isfinite
from urllib.parse import urlencode

from config import ConfigurationError, require_api_key
from stock_tracker.exceptions import (
    ProviderAccessError, ProviderAuthenticationError, ProviderRequestError,
    ProviderResponseError, ProviderTimeoutError, ProviderUnavailableError, RateLimitError,
)
from .transport import HttpTransport, ProviderPolicy, _TransportConnectionError, _TransportTimeout


logger = logging.getLogger(__name__)
_ROUTES = frozenset({"quote", "profile", "stock-price-change", "search-symbol"})


def _reject_constant(value: str) -> None:
    raise ProviderResponseError()


def _utc(clock: Callable[[], datetime]) -> datetime:
    value = clock()
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("Provider clock must return an aware UTC datetime.")
    return value


def _retry_after(headers: Mapping[str, str], clock: Callable[[], datetime]) -> float | None:
    value = next((value for key, value in headers.items() if key.lower() == "retry-after"), None)
    if value is None:
        return None
    value = value.strip()
    try:
        if value.isascii() and value.isdecimal():
            delay = float(int(value))
            return delay if isfinite(delay) else None
        else:
            stamp = parsedate_to_datetime(value)
            if stamp.tzinfo is None:
                return None
    except (ValueError, OverflowError, TypeError):
        return None
    delay = max(0.0, (stamp - _utc(clock)).total_seconds())
    return delay if isfinite(delay) else None


class FMPMarketDataProvider:
    """Injected common machinery only; does not yet claim provider capabilities."""

    def __init__(
        self, *, api_key: str, transport: HttpTransport, policy: ProviderPolicy,
        clock: Callable[[], datetime], monotonic: Callable[[], float],
        sleep: Callable[[float], None], jitter: Callable[[float], float],
    ) -> None:
        if not isinstance(api_key, str):
            raise ConfigurationError("Market-data credential must be a valid header value.")
        key = require_api_key(api_key)
        if any(ord(char) < 32 or ord(char) >= 127 for char in key):
            raise ConfigurationError("Market-data credential must be a valid header value.")
        if not isinstance(policy, ProviderPolicy) or not callable(getattr(transport, "get", None)):
            raise ValueError("Provider requires approved policy and an HTTP transport.")
        if not all(callable(item) for item in (clock, monotonic, sleep, jitter)):
            raise ValueError("Provider requires explicit clock, monotonic, sleep and jitter callables.")
        self._api_key, self._transport, self._policy = key, transport, policy
        self._clock, self._monotonic, self._sleep, self._jitter = clock, monotonic, sleep, jitter

    def __reduce_ex__(self, protocol):
        raise TypeError("Market-data providers cannot be serialized.")

    def _request_json(self, operation: str, parameters: Mapping[str, str]) -> tuple[list[dict], datetime]:
        """One approved route and bounded retry loop, without endpoint field parsing."""
        if (not isinstance(operation, str) or operation not in _ROUTES
                or not isinstance(parameters, Mapping)
                or any(not isinstance(key, str) or not isinstance(value, str)
                       or key not in {"symbol", "query", "limit", "exchange"}
                       for key, value in parameters.items())):
            raise ProviderRequestError()
        url = "https://financialmodelingprep.com/stable/" + operation + "?" + urlencode(parameters)
        started = self._monotonic()
        for attempt in range(1, self._policy.max_attempts + 1):
            remaining = self._remaining(started)
            if remaining <= 0:
                raise ProviderTimeoutError()
            status = None
            failure = "unavailable"
            try:
                response = self._transport.get(
                    url, headers={"apikey": self._api_key},
                    timeout_seconds=min(self._policy.timeout_seconds, remaining),
                )
            except _TransportTimeout:
                failure = "timeout"
            except _TransportConnectionError as error:
                if not error.retryable:
                    logger.warning("Market-data request failed.", extra={"operation": operation,
                                   "category": "connection", "attempt": attempt})
                    raise ProviderUnavailableError() from None
                failure = "connection"
            else:
                status = response.status
                if status == 200:
                    received = _utc(self._clock)
                    try:
                        payload = json.loads(response.body.decode("utf-8"), parse_float=Decimal,
                                             parse_int=int, parse_constant=_reject_constant)
                    except (UnicodeDecodeError, ValueError, InvalidOperation):
                        raise ProviderResponseError() from None
                    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
                        raise ProviderResponseError()
                    return payload, received
                logger.warning("Market-data request failed.", extra={"operation": operation,
                               "category": "http", "status": status, "attempt": attempt})
                if status == 429:
                    raise RateLimitError(retry_after_seconds=_retry_after(response.headers, self._clock))
                error_class = {401: ProviderAuthenticationError, 402: ProviderAccessError,
                               403: ProviderAccessError, 400: ProviderRequestError,
                               422: ProviderRequestError}.get(status)
                if error_class is not None:
                    raise error_class()
                if status not in self._policy.retryable_statuses:
                    raise ProviderUnavailableError()
            if attempt == self._policy.max_attempts:
                logger.warning("Market-data retries exhausted.", extra={"operation": operation,
                               "category": failure, "attempt": attempt})
                raise (ProviderTimeoutError() if failure == "timeout" else ProviderUnavailableError()) from None
            upper = min(self._policy.backoff_cap_seconds,
                        self._policy.backoff_base_seconds * 2 ** (attempt - 1))
            delay = self._jitter(upper)
            if not isinstance(delay, (int, float)) or isinstance(delay, bool) or not isfinite(delay) or not 0 <= delay <= upper:
                raise ValueError("Provider jitter must be finite and within its approved bounds.")
            remaining = self._remaining(started)
            if remaining <= 0 or delay >= remaining:
                raise ProviderTimeoutError()
            logger.warning("Retrying market-data request.", extra={"operation": operation,
                           "category": failure, "attempt": attempt})
            self._sleep(delay)
        raise AssertionError("Approved attempt loop did not return or raise")

    def _remaining(self, started: float) -> float:
        current = self._monotonic()
        if (not isinstance(started, (int, float)) or isinstance(started, bool)
                or not isinstance(current, (int, float)) or isinstance(current, bool)
                or not isfinite(started) or not isfinite(current) or current < started):
            raise ValueError("Provider monotonic clock must return finite ordered values.")
        return self._policy.retry_budget_seconds - (current - started)
