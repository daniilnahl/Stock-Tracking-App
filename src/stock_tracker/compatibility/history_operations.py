"""Historical facade orchestration, separate from holdings and chart rendering."""

from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone

from stock_tracker.exceptions import (
    HistoryRangeError, InvalidTickerError, MarketDataUnavailableError, ProviderResponseError,
)
from stock_tracker.providers import factory as provider_factory
from stock_tracker.providers.models import PriceBar, _symbol


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
    if (start is None) != (end is None):
        raise HistoryRangeError()
    if start is not None and (type(start) is not date or type(end) is not date):
        raise HistoryRangeError()
    now = (clock or utc_now)()
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise HistoryRangeError()
    if start is None:
        try:
            end = now.date() - timedelta(days=1)
            year = end.year - 5
            day = 28 if end.month == 2 and end.day == 29 else end.day
            start = date(year, end.month, day)
        except (OverflowError, ValueError):
            raise HistoryRangeError() from None
    if start > end or (end - start).days >= 3660 or end >= now.date():
        raise HistoryRangeError()
    return start, end


def get_price_history(stock, *, start: date | None = None, end: date | None = None) -> list[PriceBar]:
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
    if not isinstance(bars, list):
        raise ProviderResponseError()
    if not bars:
        raise MarketDataUnavailableError()
    previous = None
    for bar in bars:
        if not isinstance(bar, PriceBar):
            raise ProviderResponseError()
        bar.__post_init__()
        if bar.symbol != symbol:
            raise ProviderResponseError(field="symbol")
        if not start <= bar.date <= end or previous is not None and bar.date <= previous:
            raise ProviderResponseError(field="date")
        if bar.adjusted_close is not None:
            raise ProviderResponseError(field="adjusted_close")
        if bar.volume is not None and bar.volume > 9223372036854775807:
            raise ProviderResponseError(field="volume")
        previous = bar.date
    return list(bars)
