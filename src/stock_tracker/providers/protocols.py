"""Provider capabilities, independent of transport and provider schemas."""

from datetime import date
from typing import Protocol

from .models import CompanyProfile, InstrumentIdentity, PeriodChanges, PriceBar, Quote


class MarketDataProvider(Protocol):
    """Current identity, quote, profile and legacy summary capabilities."""

    def resolve_symbol(self, symbol: str) -> InstrumentIdentity: ...

    def get_quote(self, symbol: str) -> Quote: ...

    def get_company_profile(self, symbol: str) -> CompanyProfile: ...

    def get_period_changes(self, symbol: str) -> PeriodChanges: ...


class HistoricalMarketDataProvider(Protocol):
    """M4 retrieval capability; M2 does not provide its implementation."""

    def get_price_history(self, symbol: str, start: date, end: date) -> list[PriceBar]: ...
