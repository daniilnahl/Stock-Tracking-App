"""Safe application failure categories; no raw provider input in messages."""

from math import isfinite


class StockTrackerError(Exception):
    """Base application failure with a fixed, safe diagnostic."""

    _message = "Stock tracking operation failed."

    def __init__(self) -> None:
        super().__init__(self._message)


class PersistenceError(StockTrackerError):
    """Local database or filesystem failure without raw storage diagnostics."""

    _message = "Local storage operation failed."


class PersistenceValidationError(PersistenceError):
    """Invalid supplied storage or transfer candidate."""

    _message = "Local storage input is invalid."


class PersistenceDataError(PersistenceError):
    """Stored data violates the accepted application contract."""

    _message = "Local storage data is invalid."


class PersistenceConflictError(PersistenceError):
    """Explicit creation or transfer collides with an existing record."""

    _message = "Local storage record already exists."


class PersistenceNotFoundError(PersistenceError):
    """An update requires an existing target."""

    _message = "Local storage record was not found."


class SchemaVersionError(PersistenceError):
    """Schema shape or version cannot be safely used."""

    _message = "Local storage schema is unsupported."


class LegacyStatePresentError(PersistenceError):
    """Legacy state prevents an implicit empty replacement."""

    _message = "Legacy state requires an explicit safe transition before saving."


class InvalidTickerError(StockTrackerError):
    """Local input or a validated lookup is invalid in the supported scope."""

    _message = "Ticker input is invalid."


class MarketDataUnavailableError(StockTrackerError):
    """Requested market data is unavailable."""

    _message = "Market data is unavailable."


class InstrumentLookupInconclusiveError(MarketDataUnavailableError):
    """Scoped lookup did not establish an exact supported identity."""

    _message = "No exact instrument was found in the supported NASDAQ scope."


class ProviderUnavailableError(StockTrackerError):
    """Provider infrastructure or an endpoint is unavailable."""

    _message = "Market-data provider is unavailable."


class ProviderTimeoutError(ProviderUnavailableError):
    """Provider request timed out or its retry admission window expired."""

    _message = "Market-data request timed out."


class RateLimitError(StockTrackerError):
    """Rate limit, with an optional safe delay diagnostic, never an auto-retry."""

    _message = "Market-data rate limit reached."

    def __init__(self, *, retry_after_seconds: float | None = None) -> None:
        if retry_after_seconds is not None and (
            not isinstance(retry_after_seconds, float)
            or not isfinite(retry_after_seconds)
            or retry_after_seconds < 0
        ):
            raise ValueError("retry_after_seconds must be a finite nonnegative float or None.")
        self.retry_after_seconds = retry_after_seconds
        super().__init__()


class ProviderAuthenticationError(StockTrackerError):
    """Provider authentication was denied."""

    _message = "Market-data provider authentication failed."


class ProviderAccessError(StockTrackerError):
    """Provider entitlement or access was denied."""

    _message = "Market-data provider access was denied."


class ProviderRequestError(StockTrackerError):
    """Provider rejected the request, without proving an invalid ticker."""

    _message = "Market-data provider rejected the request."


_RESPONSE_FIELDS = frozenset({
    "symbol", "exchange", "name", "currency", "price", "as_of", "retrieved_at",
    "sector", "country", "market_cap", "day_1", "day_5", "month_1", "month_3",
    "month_6", "year_1", "year_3", "year_5", "date", "open", "high", "low",
    "close", "adjusted_close", "volume", "companyName", "marketCap", "timestamp",
    "1D", "5D", "1M", "3M", "6M", "1Y", "3Y", "5Y",
})


class ProviderResponseError(StockTrackerError):
    """Malformed response or model input; only approved field names are safe."""

    _message = "Market-data response is malformed."

    def __init__(self, *, field: str | None = None) -> None:
        if field is not None and (not isinstance(field, str) or field not in _RESPONSE_FIELDS):
            raise ValueError("field must name a supported provider field or be None.")
        self.field = field
        if field is None:
            super().__init__()
        else:
            Exception.__init__(self, f"Market-data response has invalid {field}.")
