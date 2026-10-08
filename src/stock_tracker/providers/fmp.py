"""FMP typed retrieval, scoped identity lookup and shared safe requests."""

from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
import json
import logging
from math import isfinite
from urllib.parse import urlencode

from config import ConfigurationError, require_api_key
from stock_tracker.exceptions import (
    HistoryRangeError, InvalidTickerError, MarketDataUnavailableError,
    ProviderAccessError, ProviderAuthenticationError, ProviderRequestError,
    ProviderResponseError, ProviderTimeoutError, ProviderUnavailableError, RateLimitError,
)
from .models import CompanyProfile, HistoryObservation, InstrumentIdentity, PeriodChanges, PriceBar, Quote
from .transport import HttpTransport, ProviderPolicy, _TransportConnectionError, _TransportTimeout


logger = logging.getLogger(__name__)
_HISTORY_ROUTE = "historical-price-eod/non-split-adjusted"
_ROUTES = frozenset({"quote", "profile", "stock-price-change", "search-symbol", _HISTORY_ROUTE})
_PERIOD_FIELDS = (("1D", "day_1"), ("5D", "day_5"), ("1M", "month_1"),
                  ("3M", "month_3"), ("6M", "month_6"), ("1Y", "year_1"),
                  ("3Y", "year_3"), ("5Y", "year_5"))


def _input_symbol(value: str) -> str:
    if not isinstance(value, str):
        raise InvalidTickerError()
    symbol = value.strip().upper()
    if not symbol or any(char.isspace() or ord(char) < 32 or 127 <= ord(char) <= 159
                         or char == ',' for char in symbol):
        raise InvalidTickerError()
    return symbol


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProviderResponseError(field=field)
    return value if value.strip() else None


def _number(value: object, field: str = "price", *, nonnegative: bool = True) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not int and not isinstance(value, Decimal):
        raise ProviderResponseError(field=field)
    number = Decimal(value)
    if not number.is_finite() or (nonnegative and number < 0):
        raise ProviderResponseError(field=field)
    return number


def _market_time(value: object) -> datetime | None:
    if value is None:
        return None
    if type(value) is not int and not isinstance(value, Decimal):
        raise ProviderResponseError(field="timestamp")
    number = Decimal(value)
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        raise ProviderResponseError(field="timestamp")
    # Bound before conversion: avoids allocating a giant integer from a remote
    # Decimal exponent. Integer arithmetic preserves seconds without float rounding.
    if number > 253402300799:
        raise ProviderResponseError(field="timestamp")
    try:
        return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=int(number))
    except (ValueError, OverflowError):
        raise ProviderResponseError(field="timestamp") from None


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
    """Injected market-data adapter with exact NASDAQ identity lookup."""

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

    def get_quote(self, symbol: str) -> Quote:
        requested = _input_symbol(symbol)
        rows, received = self._request_json("quote", {"symbol": requested})
        if not rows:
            raise MarketDataUnavailableError()
        if len(rows) != 1:
            raise ProviderResponseError()
        row = rows[0]
        if row.get("symbol") != requested:
            raise ProviderResponseError(field="symbol")
        if "price" not in row:
            raise ProviderResponseError(field="price")
        return Quote(requested, _number(row["price"]),
                     _optional_text(row.get("exchange"), "exchange"),
                     _optional_text(row.get("currency"), "currency"),
                     _market_time(row.get("timestamp")), received)

    def get_company_profile(self, symbol: str) -> CompanyProfile:
        requested = _input_symbol(symbol)
        rows, received = self._request_json("profile", {"symbol": requested})
        if not rows:
            raise MarketDataUnavailableError()
        if len(rows) != 1:
            raise ProviderResponseError()
        row = rows[0]
        if row.get("symbol") != requested:
            raise ProviderResponseError(field="symbol")
        for field in ("companyName", "price", "marketCap"):
            if field not in row:
                raise ProviderResponseError(field=field)
        return CompanyProfile(requested, row["companyName"],
                              _optional_text(row.get("exchange"), "exchange"),
                              _optional_text(row.get("currency"), "currency"),
                              _optional_text(row.get("sector"), "sector"),
                              _optional_text(row.get("country"), "country"),
                              _number(row["price"]), _number(row["marketCap"], "market_cap"),
                              None, received)

    def get_period_changes(self, symbol: str) -> PeriodChanges:
        requested = _input_symbol(symbol)
        rows, received = self._request_json("stock-price-change", {"symbol": requested})
        if not rows:
            raise MarketDataUnavailableError()
        if len(rows) != 1:
            raise ProviderResponseError()
        row = rows[0]
        if row.get("symbol") != requested:
            raise ProviderResponseError(field="symbol")
        # These are provider-reported percentage points, not a calculated return
        # ratio or a history series. Validate every field before publishing.
        values = {field: _number(row.get(key), field, nonnegative=False)
                  for key, field in _PERIOD_FIELDS}
        return PeriodChanges(symbol=requested, **values, as_of=None, retrieved_at=received)

    def resolve_symbol(self, symbol: str) -> InstrumentIdentity:
        requested = _input_symbol(symbol)
        rows, _ = self._request_json("search-symbol", {"query": requested, "limit": "100", "exchange": "NASDAQ"})
        matches = []
        for row in rows:
            if "symbol" not in row:
                raise ProviderResponseError(field="symbol")
            exchange = row.get("exchange")
            if not isinstance(exchange, str) or not exchange.strip():
                raise ProviderResponseError(field="exchange")
            identity = InstrumentIdentity(row["symbol"], exchange,
                                          _optional_text(row.get("name"), "name"),
                                          _optional_text(row.get("currency"), "currency"))
            if identity.symbol == requested and identity.exchange == "NASDAQ":
                matches.append(identity)
        if len(matches) > 1:
            raise ProviderResponseError()
        if not matches:
            raise InvalidTickerError()
        return matches[0]

    def get_price_history(self, symbol: str, start: date, end: date) -> list[PriceBar]:
        """Return precise raw observations, without adjusted-return semantics."""
        return list(self._load_price_history(symbol, start, end).bars)

    def _load_price_history(self, symbol: str, start: date, end: date) -> HistoryObservation:
        """Retain the transport receipt timestamp for the future cache decorator."""
        requested = _input_symbol(symbol)
        if (not isinstance(start, date) or isinstance(start, datetime)
                or not isinstance(end, date) or isinstance(end, datetime)
                or start > end or (end - start).days + 1 > 3660
                or end >= _utc(self._clock).date()):
            raise HistoryRangeError()
        rows, received = self._request_json(
            _HISTORY_ROUTE, {"symbol": requested, "from": start.isoformat(), "to": end.isoformat()},
        )
        if len(rows) > 5000:
            raise ProviderResponseError()
        bars = []
        seen = set()
        for row in rows:
            if row.get("symbol") != requested:
                raise ProviderResponseError(field="symbol")
            value = row.get("date")
            if not isinstance(value, str):
                raise ProviderResponseError(field="date")
            try:
                session = date.fromisoformat(value)
            except ValueError:
                raise ProviderResponseError(field="date") from None
            if session.isoformat() != value or session in seen:
                raise ProviderResponseError(field="date")
            seen.add(session)
            prices = []
            for field in ("adjOpen", "adjHigh", "adjLow", "adjClose"):
                number = _number(row.get(field), field)
                if number is None:
                    raise ProviderResponseError(field=field)
                prices.append(number)
            volume = _number(row.get("volume"), "volume")
            if volume is not None and (
                volume > 9223372036854775807 or volume != volume.to_integral_value()
            ):
                raise ProviderResponseError(field="volume")
            bar = PriceBar(requested, session, *prices, None,
                           None if volume is None else int(volume))
            # Validate even observations outside the inclusive application range.
            if start <= session <= end:
                bars.append(bar)
        if not bars:
            raise MarketDataUnavailableError()
        return HistoryObservation(tuple(sorted(bars, key=lambda bar: bar.date)), received)

    def _request_json(self, operation: str, parameters: Mapping[str, str]) -> tuple[list[dict], datetime]:
        """One approved route and bounded retry loop, without endpoint field parsing."""
        if (not isinstance(operation, str) or operation not in _ROUTES
                or not isinstance(parameters, Mapping)
                or any(not isinstance(key, str) or not isinstance(value, str)
                       or key not in {"symbol", "query", "limit", "exchange", "from", "to"}
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
