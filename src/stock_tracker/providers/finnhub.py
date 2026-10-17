"""Opt-in Finnhub Free upcoming earnings-calendar EPS observations."""

from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import json
from math import isfinite
from urllib.parse import urlencode

from stock_tracker.exceptions import (
    ProviderAccessError, ProviderAuthenticationError, ProviderRequestError,
    ProviderResponseError, ProviderTimeoutError, ProviderUnavailableError, RateLimitError,
)
from .eps import UpcomingEpsEstimate
from .models import _symbol, _time
from .transport import HttpResponse, HttpTransport, _TransportConnectionError, _TransportTimeout


def _reject_constant(value: str) -> None:
    raise ProviderResponseError()


def _number(value: object) -> Decimal | None:
    if value is None:
        return None
    if type(value) not in (int, Decimal):
        raise ProviderResponseError()
    number = Decimal(value)
    if not number.is_finite():
        raise ProviderResponseError()
    return number


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProviderResponseError()
        result[key] = value
    return result


class FinnhubUpcomingEpsProvider:
    """Single-call adapter; no environment, fallback, cache or default wiring."""

    __slots__ = ("_api_key", "_transport", "_clock", "_timeout_seconds",
                 "_max_response_bytes", "_max_rows")

    def __init__(
        self, *, api_key: str, transport: HttpTransport, clock: Callable[[], datetime],
        timeout_seconds: float, max_response_bytes: int, max_rows: int,
    ) -> None:
        if (not isinstance(api_key, str) or not api_key.strip()
                or api_key != api_key.strip()
                or any(ord(char) < 32 or ord(char) >= 127 for char in api_key)):
            raise ValueError("Provider credential must be a valid header value.")
        if (type(timeout_seconds) is not float or not isfinite(timeout_seconds)
                or timeout_seconds <= 0
                or type(max_response_bytes) is not int or max_response_bytes < 1
                or type(max_rows) is not int or max_rows < 1
                or not callable(clock) or not callable(getattr(transport, "get", None))):
            raise ValueError("Provider requires explicit valid bounds, clock and transport.")
        self._api_key = api_key
        self._transport = transport
        self._clock = clock
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._max_rows = max_rows

    def __reduce_ex__(self, protocol):
        raise TypeError("Market-data providers cannot be serialized.")

    def get_upcoming_eps(
        self, symbol: str, *, start: date, end: date, analysis_date: date,
    ) -> tuple[UpcomingEpsEstimate, ...]:
        try:
            _symbol(symbol)
        except ProviderResponseError:
            raise ProviderRequestError() from None
        if (any(type(value) is not date for value in (start, end, analysis_date))
                or not analysis_date < start <= end):
            raise ProviderRequestError()
        try:
            query = urlencode({"symbol": symbol, "from": start.isoformat(), "to": end.isoformat(),
                               "international": "false"})
        except UnicodeEncodeError:
            raise ProviderRequestError() from None
        try:
            response = self._transport.get(
                "https://finnhub.io/api/v1/calendar/earnings?" + query,
                headers={"X-Finnhub-Token": self._api_key}, timeout_seconds=self._timeout_seconds,
            )
        except _TransportTimeout:
            raise ProviderTimeoutError() from None
        except _TransportConnectionError:
            raise ProviderUnavailableError() from None
        if not isinstance(response, HttpResponse):
            raise ProviderResponseError()
        status = response.status
        if status == 401:
            raise ProviderAuthenticationError()
        if status in (402, 403):
            raise ProviderAccessError()
        if status == 429:
            raise RateLimitError()
        if status == 408:
            raise ProviderTimeoutError()
        if status >= 500:
            raise ProviderUnavailableError()
        if status != 200:
            raise ProviderRequestError()
        if len(response.body) > self._max_response_bytes:
            raise ProviderResponseError()
        try:
            payload = json.loads(response.body.decode("utf-8"), parse_float=Decimal,
                                 parse_constant=_reject_constant, object_pairs_hook=_unique_object)
        except (UnicodeDecodeError, ValueError, InvalidOperation, RecursionError):
            raise ProviderResponseError() from None
        if not isinstance(payload, dict) or "error" in payload:
            raise ProviderResponseError()
        rows = payload.get("earningsCalendar")
        if not isinstance(rows, list) or len(rows) > self._max_rows:
            raise ProviderResponseError()
        received = self._clock()
        _time(received, "retrieved_at", optional=False)
        result = []
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or row.get("symbol") != symbol:
                raise ProviderResponseError()
            raw_date = row.get("date")
            if not isinstance(raw_date, str):
                raise ProviderResponseError()
            try:
                release = date.fromisoformat(raw_date)
            except ValueError:
                raise ProviderResponseError() from None
            if raw_date != release.isoformat() or not start <= release <= end:
                raise ProviderResponseError()
            if "epsActual" not in row or "epsEstimate" not in row:
                raise ProviderResponseError()
            actual, estimate = _number(row["epsActual"]), _number(row["epsEstimate"])
            session = row.get("hour")
            if isinstance(session, str) and not session.strip():
                session = None
            observation = UpcomingEpsEstimate(symbol, row.get("year"), row.get("quarter"),
                                             release, session, estimate, received)
            identity = (observation.fiscal_year, observation.fiscal_quarter)
            if identity in seen:
                raise ProviderResponseError()
            seen.add(identity)
            if actual is None:
                result.append(observation)
        return tuple(sorted(result, key=lambda item: (
            item.release_date, item.fiscal_year, item.fiscal_quarter,
        )))
