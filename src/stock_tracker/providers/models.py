"""Immutable numeric provider models under accepted ADR-0007."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from stock_tracker.exceptions import ProviderResponseError


def _symbol(value: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.upper()
        or any(char.isspace() or ord(char) < 32 or 127 <= ord(char) <= 159 or char == ","
               for char in value)
    ):
        raise ProviderResponseError(field="symbol")


def _text(value: str | None, field: str, *, optional: bool = True) -> None:
    if optional and value is None:
        return
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ProviderResponseError(field=field)


def _decimal(
    value: Decimal | None, field: str, *, optional: bool = True, nonnegative: bool = True,
) -> None:
    if optional and value is None:
        return
    if (not isinstance(value, Decimal) or not value.is_finite()
            or (nonnegative and value < 0)):
        raise ProviderResponseError(field=field)


def _time(value: datetime | None, field: str, *, optional: bool = True) -> None:
    if optional and value is None:
        return
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ProviderResponseError(field=field)


@dataclass(frozen=True, slots=True)
class InstrumentIdentity:
    """Provider identity metadata, without inventing an exchange or currency."""

    symbol: str
    exchange: str | None
    name: str | None
    currency: str | None

    def __post_init__(self) -> None:
        _symbol(self.symbol)
        for field in ("exchange", "name", "currency"):
            _text(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class Quote:
    """Per-share price; client receipt time is distinct from market time."""

    symbol: str
    price: Decimal | None
    exchange: str | None
    currency: str | None
    as_of: datetime | None
    retrieved_at: datetime

    def __post_init__(self) -> None:
        _symbol(self.symbol)
        _decimal(self.price, "price")
        _text(self.exchange, "exchange")
        _text(self.currency, "currency")
        _time(self.as_of, "as_of")
        _time(self.retrieved_at, "retrieved_at", optional=False)


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    """Unformatted company metadata and nullable numeric profile values."""

    symbol: str
    name: str
    exchange: str | None
    currency: str | None
    sector: str | None
    country: str | None
    price: Decimal | None
    market_cap: Decimal | None
    as_of: datetime | None
    retrieved_at: datetime

    def __post_init__(self) -> None:
        _symbol(self.symbol)
        _text(self.name, "name", optional=False)
        for field in ("exchange", "currency", "sector", "country"):
            _text(getattr(self, field), field)
        _decimal(self.price, "price")
        _decimal(self.market_cap, "market_cap")
        _time(self.as_of, "as_of")
        _time(self.retrieved_at, "retrieved_at", optional=False)


@dataclass(frozen=True, slots=True)
class PeriodChanges:
    """Provider-reported percentage points, never reconstructed price history."""

    symbol: str
    day_1: Decimal | None
    day_5: Decimal | None
    month_1: Decimal | None
    month_3: Decimal | None
    month_6: Decimal | None
    year_1: Decimal | None
    year_3: Decimal | None
    year_5: Decimal | None
    as_of: datetime | None
    retrieved_at: datetime

    def __post_init__(self) -> None:
        _symbol(self.symbol)
        for field in ("day_1", "day_5", "month_1", "month_3", "month_6",
                      "year_1", "year_3", "year_5"):
            _decimal(getattr(self, field), field, nonnegative=False)
        _time(self.as_of, "as_of")
        _time(self.retrieved_at, "retrieved_at", optional=False)


@dataclass(frozen=True, slots=True)
class PriceBar:
    """Future history contract; date is a trading-session label, not UTC midnight."""

    symbol: str
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal | None
    volume: int | None

    def __post_init__(self) -> None:
        _symbol(self.symbol)
        if not isinstance(self.date, date) or isinstance(self.date, datetime):
            raise ProviderResponseError(field="date")
        for field in ("open", "high", "low", "close"):
            _decimal(getattr(self, field), field, optional=False)
        _decimal(self.adjusted_close, "adjusted_close")
        if self.volume is not None and (
            not isinstance(self.volume, int) or isinstance(self.volume, bool) or self.volume < 0
        ):
            raise ProviderResponseError(field="volume")
