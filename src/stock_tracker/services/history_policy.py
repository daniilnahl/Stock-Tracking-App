"""Pure accepted historical request and raw-observation validation."""

from collections.abc import Callable
from datetime import date, datetime, timedelta

from stock_tracker.exceptions import HistoryRangeError, MarketDataUnavailableError, ProviderResponseError
from stock_tracker.providers.models import PriceBar


def resolve_history_range(
    start: date | None = None, end: date | None = None,
    *, clock: Callable[[], datetime],
) -> tuple[date, date]:
    if (start is None) != (end is None):
        raise HistoryRangeError()
    if start is not None and (type(start) is not date or type(end) is not date):
        raise HistoryRangeError()
    now = clock()
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


def validated_raw_bars(bars: list[PriceBar], symbol: str, start: date, end: date) -> tuple[PriceBar, ...]:
    if not isinstance(bars, list):
        raise ProviderResponseError()
    if not bars:
        raise MarketDataUnavailableError()
    previous = None
    for bar in bars:
        if not isinstance(bar, PriceBar):
            raise ProviderResponseError()
        PriceBar.__post_init__(bar)
        if bar.symbol != symbol:
            raise ProviderResponseError(field="symbol")
        if not start <= bar.date <= end or previous is not None and bar.date <= previous:
            raise ProviderResponseError(field="date")
        if bar.adjusted_close is not None:
            raise ProviderResponseError(field="adjusted_close")
        if bar.volume is not None and bar.volume > 9223372036854775807:
            raise ProviderResponseError(field="volume")
        previous = bar.date
    return tuple(bars)
