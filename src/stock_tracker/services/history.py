"""Injected historical retrieval; raw numeric observations without presentation."""

from collections.abc import Callable
from datetime import date, datetime

from stock_tracker.domain import DomainValidationError, Stock
from stock_tracker.exceptions import HistoryRangeError, InvalidTickerError, MarketDataUnavailableError, PersistenceValidationError, ProviderResponseError
from .history_policy import resolve_history_range, validated_raw_bars
from stock_tracker.providers.models import _symbol
from .models import HistoryView
from .protocols import HistoricalProviderSource


class HistoryService:
    def __init__(self, providers: HistoricalProviderSource, *, clock: Callable[[], datetime]) -> None:
        self._providers, self._clock = providers, clock

    def validate_range(self, start: date, end: date) -> tuple[date, date]:
        if type(start) is not date or type(end) is not date:
            raise HistoryRangeError()
        return resolve_history_range(start, end, clock=self._clock)

    def history(
        self, stock: Stock, *, ordinal: int,
        start: date | None = None, end: date | None = None,
    ) -> HistoryView:
        if not isinstance(stock, Stock):
            raise DomainValidationError("stock must be a Stock.")
        Stock.__post_init__(stock)
        if stock.exchange != "NASDAQ":
            raise MarketDataUnavailableError()
        if type(ordinal) is not int or ordinal < 0:
            raise PersistenceValidationError()
        first, last = resolve_history_range(start, end, clock=self._clock)
        symbol = stock.symbol.upper()
        try:
            _symbol(symbol)
        except ProviderResponseError:
            raise InvalidTickerError() from None
        bars = self._providers(ordinal).get_price_history(symbol, first, last)
        return HistoryView(stock, first, last, validated_raw_bars(bars, symbol, first, last))
