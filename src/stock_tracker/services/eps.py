"""Injected upcoming EPS requests with explicit intended-date provenance."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from stock_tracker.exceptions import ProviderRequestError, ProviderResponseError, ProviderUnavailableError, UpcomingEpsInputError
from stock_tracker.providers.eps import UpcomingEpsEstimate, UpcomingEpsProvider
from stock_tracker.providers.models import _symbol


def _request_inputs(symbol: str, start: date, end: date) -> None:
    try:
        _symbol(symbol)
        symbol.encode("utf-8")
    except (ProviderResponseError, UnicodeEncodeError):
        raise UpcomingEpsInputError() from None
    if type(start) is not date or type(end) is not date or start > end:
        raise UpcomingEpsInputError()


@dataclass(frozen=True, slots=True)
class UpcomingEpsView:
    """One request and its unchanged observations, without completeness claims."""

    symbol: str
    start: date
    end: date
    analysis_date: date
    observations: tuple[UpcomingEpsEstimate, ...]

    def __post_init__(self) -> None:
        try:
            _request_inputs(self.symbol, self.start, self.end)
        except ProviderRequestError:
            raise ProviderResponseError() from None
        if (type(self.analysis_date) is not date or not self.analysis_date < self.start
                or type(self.observations) is not tuple):
            raise ProviderResponseError()
        periods = set()
        previous = None
        for observation in self.observations:
            if type(observation) is not UpcomingEpsEstimate:
                raise ProviderResponseError()
            try:
                UpcomingEpsEstimate.__post_init__(observation)
                if (observation.symbol != self.symbol
                        or not self.start <= observation.release_date <= self.end):
                    raise ProviderResponseError()
                for field, expected in (
                    ("provider", "finnhub"), ("source", "earnings_calendar"),
                    ("source_field", "epsEstimate"), ("accounting_basis", "non-GAAP"),
                    ("units", "currency-per-share"),
                ):
                    supplied = getattr(observation, field, None)
                    if type(supplied) is not str or supplied != expected:
                        raise ProviderResponseError()
                for field in ("currency", "share_basis", "published_at", "fiscal_period_end"):
                    if getattr(observation, field, object()) is not None:
                        raise ProviderResponseError()
                period = (observation.fiscal_year, observation.fiscal_quarter)
                order = (observation.release_date, *period)
            except AttributeError:
                raise ProviderResponseError() from None
            if period in periods or (previous is not None and order <= previous):
                raise ProviderResponseError()
            periods.add(period)
            previous = order


class UpcomingEpsService:
    """One lazy provider call using one explicitly injected research date."""

    def __init__(
        self, providers: Callable[[], UpcomingEpsProvider], *, research_date: Callable[[], date],
    ) -> None:
        if not callable(providers) or not callable(research_date):
            raise ValueError("EPS service requires provider and research-date callables.")
        self._providers, self._research_date = providers, research_date

    def upcoming_eps(self, symbol: str, *, start: date, end: date) -> UpcomingEpsView:
        _request_inputs(symbol, start, end)
        analysis_date = self._research_date()
        if type(analysis_date) is not date:
            raise ProviderUnavailableError()
        if not analysis_date < start:
            raise UpcomingEpsInputError()
        provider = self._providers()
        if not callable(getattr(provider, "get_upcoming_eps", None)):
            raise ProviderResponseError()
        observations = provider.get_upcoming_eps(symbol, start=start, end=end, analysis_date=analysis_date)
        return UpcomingEpsView(symbol, start, end, analysis_date, observations)
