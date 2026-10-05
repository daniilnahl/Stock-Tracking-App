"""Immutable local-storage records under accepted ADR-0009; no IO or mapping."""

from dataclasses import dataclass
from decimal import Decimal

from stock_tracker.domain import Stock
from stock_tracker.exceptions import PersistenceValidationError


@dataclass(frozen=True, slots=True)
class WatchlistEntry:
    """Preserve optional ownership and legacy display metadata without inference."""

    stock: Stock
    quantity: Decimal
    average_cost: Decimal | None
    current_price: Decimal | None
    sector: str | None
    country: str | None
    currency: str | None
    market_cap: str | None
    price_1d: str | None
    price_5d: str | None
    price_30d: str | None
    price_3m: str | None
    price_6m: str | None
    price_1y: str | None
    price_3y: str | None
    price_5y: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.stock, Stock):
            raise PersistenceValidationError()
        for value, optional in (
            (self.quantity, False), (self.average_cost, True), (self.current_price, True),
        ):
            if optional and value is None:
                continue
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise PersistenceValidationError()
        if self.average_cost is None and self.quantity != 0:
            raise PersistenceValidationError()
        for field in (
            "sector", "country", "currency", "market_cap", "price_1d", "price_5d",
            "price_30d", "price_3m", "price_6m", "price_1y", "price_3y", "price_5y",
        ):
            value = getattr(self, field)
            if value is not None and not isinstance(value, str):
                raise PersistenceValidationError()


@dataclass(frozen=True, slots=True)
class WatchlistRecord:
    """An independent exact namespace with an immutable ordered entry tuple."""

    namespace: str
    name: str
    entries: tuple[WatchlistEntry, ...]

    def __post_init__(self) -> None:
        for value in (self.namespace, self.name):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise PersistenceValidationError()
        if not isinstance(self.entries, tuple) or any(
            not isinstance(entry, WatchlistEntry) for entry in self.entries
        ):
            raise PersistenceValidationError()
