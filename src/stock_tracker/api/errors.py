"""Fixed HTTP diagnostics; supplied values and raw exceptions never cross HTTP."""

import logging

from stock_tracker.domain.errors import DomainValidationError
from stock_tracker import exceptions as failures


logger = logging.getLogger(__name__)
ERRORS = {
    "unauthorized": (401, "Authentication is required."),
    "origin_forbidden": (403, "Browser origins are not allowed."),
    "host_invalid": (400, "Host is not allowed."),
    "invalid_request": (422, "Request input is invalid."),
    "not_found": (404, "Resource was not found."),
    "method_not_allowed": (405, "Method is not allowed."),
    "legacy_state_present": (409, "Legacy state requires an explicit safe transition."),
    "invalid_ticker": (422, "Ticker input is invalid."),
    "market_data_unavailable": (503, "Market data is unavailable."),
    "provider_timeout": (504, "Market-data request timed out."),
    "provider_rate_limited": (429, "Market-data rate limit reached."),
    "provider_response_invalid": (502, "Market-data response is invalid."),
    "provider_unavailable": (503, "Market-data provider is unavailable."),
    "internal_error": (500, "The operation failed."),
    "api_busy": (503, "API operation capacity is unavailable."),
    "response_too_large": (503, "Response exceeds the supported size."),
    "request_too_large": (414, "Request target exceeds the supported size."),
    "history_disabled": (503, "Historical acquisition is disabled."),
    "eps_disabled": (503, "Upcoming EPS acquisition is disabled."),
}


class ApiFailure(Exception):
    """A presentation failure restricted to approved constant codes."""

    def __init__(self, code: str) -> None:
        if code not in ERRORS:
            raise ValueError("Unsupported API failure code.")
        self.code = code
        super().__init__(ERRORS[code][1])


def error_code(error: Exception) -> str:
    if isinstance(error, ApiFailure):
        return error.code
    for category, code in (
        (failures.LegacyStatePresentError, "legacy_state_present"),
        (failures.HistoryRangeError, "invalid_request"),
        (failures.UpcomingEpsInputError, "invalid_request"),
        (DomainValidationError, "invalid_request"),
        (failures.InvalidTickerError, "invalid_ticker"),
        (failures.ProviderTimeoutError, "provider_timeout"),
        (failures.MarketDataUnavailableError, "market_data_unavailable"),
        (failures.RateLimitError, "provider_rate_limited"),
        (failures.ProviderResponseError, "provider_response_invalid"),
        (failures.ProviderUnavailableError, "provider_unavailable"),
        (failures.ProviderAuthenticationError, "provider_unavailable"),
        (failures.ProviderAccessError, "provider_unavailable"),
        (failures.ProviderRequestError, "provider_unavailable"),
    ):
        if isinstance(error, category):
            return code
    # Composition translates configuration failures into ApiFailure; the API
    # boundary must not import environment/configuration loaders to classify them.
    return "internal_error"


def record_failure(code: str) -> None:
    logger.warning("API operation failed: %s", code)
