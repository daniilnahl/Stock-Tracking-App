"""Accepted failure categories and safe diagnostic constructor boundaries."""

import pytest


ERRORS = (
    "StockTrackerError", "HistoryRangeError", "InvalidTickerError", "MarketDataUnavailableError",
    "InstrumentLookupInconclusiveError", "ProviderUnavailableError", "ProviderTimeoutError",
    "RateLimitError", "ProviderAuthenticationError", "ProviderAccessError",
    "ProviderRequestError", "ProviderResponseError",
)


@pytest.mark.parametrize("name", ERRORS)
def test_errors_are_safe_fixed_messages_and_do_not_accept_arbitrary_payload(name):
    from stock_tracker import exceptions

    constructor = getattr(exceptions, name)
    first = constructor()
    assert isinstance(first, exceptions.StockTrackerError)
    assert str(first) == str(constructor())
    assert first.args == (str(first),)
    assert "http" not in repr(first)
    with pytest.raises(TypeError) as caught:
        constructor("synthetic-private-input https://example.invalid/")
    assert "synthetic-private-input" not in str(caught.value)


def test_failure_inheritance_preserves_distinct_categories():
    from stock_tracker.exceptions import (
        InstrumentLookupInconclusiveError, InvalidTickerError, MarketDataUnavailableError,
        ProviderTimeoutError, ProviderUnavailableError, StockTrackerError,
    )
    from stock_tracker.domain import DomainValidationError

    assert isinstance(ProviderTimeoutError(), ProviderUnavailableError)
    unresolved = InstrumentLookupInconclusiveError()
    assert isinstance(unresolved, MarketDataUnavailableError)
    assert not isinstance(unresolved, InvalidTickerError)
    assert "NASDAQ" in str(unresolved)
    assert "invalid" not in str(unresolved).lower()
    assert not issubclass(DomainValidationError, StockTrackerError)


@pytest.mark.parametrize("delay", [None, 0.0, 1.25, 1e100])
def test_rate_limit_delay_is_safe_optional_diagnostic_without_message_leakage(delay):
    from stock_tracker.exceptions import RateLimitError

    error = RateLimitError(retry_after_seconds=delay)
    assert error.retry_after_seconds == delay
    assert str(error) == "Market-data rate limit reached."
    assert repr(error) == "RateLimitError('Market-data rate limit reached.')"


@pytest.mark.parametrize("delay", [False, True, 1, "synthetic-private-input", [], -1.0,
                                    float("nan"), float("inf"), float("-inf")])
def test_rate_limit_rejects_wrong_type_negative_or_nonfinite_delay_safely(delay):
    from stock_tracker.exceptions import RateLimitError

    with pytest.raises(ValueError) as caught:
        RateLimitError(retry_after_seconds=delay)
    assert str(caught.value) == "retry_after_seconds must be a finite nonnegative float or None."


@pytest.mark.parametrize("field", [None, "symbol", "retrieved_at", "adjusted_close",
                                    "companyName", "marketCap", "timestamp", "1D", "5Y",
                                    "adjOpen", "adjHigh", "adjLow", "adjClose"])
def test_response_error_allows_only_approved_field_diagnostics(field):
    from stock_tracker.exceptions import ProviderResponseError

    error = ProviderResponseError(field=field)
    assert error.field == field
    assert str(error) == ("Market-data response is malformed." if field is None
                          else f"Market-data response has invalid {field}.")


@pytest.mark.parametrize("field", ["synthetic-private-input", "https://example.invalid/",
                                    "api_key", "timeout_seconds", [], 1, False])
def test_response_error_never_echoes_unknown_or_unhashable_field_arguments(field):
    from stock_tracker.exceptions import ProviderResponseError

    with pytest.raises(ValueError) as caught:
        ProviderResponseError(field=field)
    assert str(caught.value) == "field must name a supported provider field or be None."
