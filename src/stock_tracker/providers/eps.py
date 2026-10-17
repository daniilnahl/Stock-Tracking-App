"""Independent upcoming-release EPS capability under ADR-0015."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from stock_tracker.exceptions import ProviderResponseError
from .models import _symbol, _time


@dataclass(frozen=True, slots=True)
class UpcomingEpsEstimate:
    """Reported non-GAAP observation, without inferred comparison inputs."""

    symbol: str
    fiscal_year: int
    fiscal_quarter: int
    release_date: date
    release_session: str | None
    estimate: Decimal | None
    retrieved_at: datetime

    provider: str = field(default="finnhub", init=False)
    source: str = field(default="earnings_calendar", init=False)
    source_field: str = field(default="epsEstimate", init=False)
    accounting_basis: str = field(default="non-GAAP", init=False)
    units: str = field(default="currency-per-share", init=False)
    currency: None = field(default=None, init=False)
    share_basis: None = field(default=None, init=False)
    published_at: None = field(default=None, init=False)
    fiscal_period_end: None = field(default=None, init=False)

    def __post_init__(self) -> None:
        _symbol(self.symbol)
        if (type(self.fiscal_year) is not int or not 1 <= self.fiscal_year <= 9999
                or type(self.fiscal_quarter) is not int or not 1 <= self.fiscal_quarter <= 4
                or type(self.release_date) is not date
                or self.release_session not in (None, "bmo", "amc", "dmh")
                or (self.estimate is not None and (
                    not isinstance(self.estimate, Decimal) or not self.estimate.is_finite()))):
            raise ProviderResponseError()
        _time(self.retrieved_at, "retrieved_at", optional=False)


class UpcomingEpsProvider(Protocol):
    """An explicit release-date request; not a historical as-of forecast feed."""

    def get_upcoming_eps(
        self, symbol: str, *, start: date, end: date, analysis_date: date,
    ) -> tuple[UpcomingEpsEstimate, ...]: ...
