"""Historical facade orchestration, separate from holdings and chart rendering."""

from collections.abc import Callable
from datetime import date, datetime, timezone

from stock_tracker.exceptions import (
    InvalidTickerError, MarketDataUnavailableError, ProviderResponseError,
)
from stock_tracker.providers import factory as provider_factory
from stock_tracker.providers.models import PriceBar, _symbol
from stock_tracker.services.history_policy import resolve_history_range as _resolve_history_range, validated_raw_bars


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_history_identity(stock) -> None:
    """Reject unsupported saved identities before credentials or external IO."""
    if stock.exchange != "NASDAQ":
        raise MarketDataUnavailableError()


def resolve_history_range(
    start: date | None = None, end: date | None = None,
    *, clock: Callable[[], datetime] | None = None,
) -> tuple[date, date]:
    """Resolve inclusive dates once, with the approved five-calendar-year default."""
    return _resolve_history_range(start, end, clock=clock or utc_now)


def get_price_history(stock, *, start: date | None = None, end: date | None = None) -> list[PriceBar]:
    return get_price_history_with_range(stock, start=start, end=end)[2]


def get_price_history_with_range(
    stock, *, start: date | None = None, end: date | None = None,
) -> tuple[date, date, list[PriceBar]]:
    """Carry the single resolved request range with its validated observations."""
    require_history_identity(stock)
    start, end = resolve_history_range(start, end)
    symbol = stock.ticker_symbol
    if not isinstance(symbol, str) or not symbol.strip():
        raise InvalidTickerError()
    symbol = symbol.strip().upper()
    try:
        _symbol(symbol)
    except ProviderResponseError:
        raise InvalidTickerError() from None
    bars = provider_factory.create_historical_market_data_provider(stock.API_KEY).get_price_history(symbol, start, end)
    return start, end, list(validated_raw_bars(bars, symbol, start, end))
