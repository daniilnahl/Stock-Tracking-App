"""Pure, explicitly currency-qualified snapshot analytics under ADR-0011."""

from dataclasses import dataclass
from decimal import Decimal

from .calculations import PositionSnapshot, position_snapshot
from .errors import (
    DomainValidationError, SnapshotCurrencyMismatchError, SnapshotCurrencyUnavailableError,
)
from .position import Position


def _currency(value: str | None, field: str, *, optional: bool = True) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DomainValidationError(f"{field} must be a nonblank currency string.")


@dataclass(frozen=True, slots=True)
class PositionValuationInput:
    """Caller assertions bind a price and separate currencies to one position."""

    position: Position
    current_price: Decimal | None
    cost_currency: str | None
    quote_currency: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.position, Position):
            raise DomainValidationError("position must be a Position.")
        price = self.current_price
        if price is not None and (
            not isinstance(price, Decimal) or not price.is_finite() or price < 0
        ):
            raise DomainValidationError("current_price must be a finite nonnegative Decimal or None.")
        _currency(self.cost_currency, "cost_currency")
        _currency(self.quote_currency, "quote_currency")


@dataclass(frozen=True, slots=True)
class PositionAllocation:
    input: PositionValuationInput
    snapshot: PositionSnapshot
    weight: Decimal | None


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    currency: str
    positions: tuple[PositionAllocation, ...]
    total_cost_basis: Decimal
    total_market_value: Decimal | None
    aggregate_unrealized_pnl: Decimal | None
    aggregate_unrealized_return: Decimal | None


def portfolio_snapshot(
    rows: tuple[PositionValuationInput, ...], *, currency: str,
) -> PortfolioSnapshot:
    """Evaluate supplied observations without IO, freshness claims or quantization."""
    _currency(currency, "currency", optional=False)
    if not isinstance(rows, tuple):
        raise DomainValidationError("rows must be a tuple of PositionValuationInput instances.")
    for row in rows:
        if not isinstance(row, PositionValuationInput):
            raise DomainValidationError("rows must contain only PositionValuationInput instances.")
        PositionValuationInput.__post_init__(row)
    for ordinal, row in enumerate(rows):
        for field in ("cost_currency", "quote_currency"):
            value = getattr(row, field)
            if value is None:
                raise SnapshotCurrencyUnavailableError(f"Row {ordinal} {field} is unavailable.")
            if value != currency:
                raise SnapshotCurrencyMismatchError(f"Row {ordinal} {field} does not match currency.")

    snapshots = tuple(position_snapshot(row.position, row.current_price) for row in rows)
    basis = sum((snapshot.cost_basis for snapshot in snapshots), Decimal(0))
    complete = all(snapshot.market_value is not None for snapshot in snapshots)
    value = sum((snapshot.market_value for snapshot in snapshots
                 if snapshot.market_value is not None), Decimal(0)) if complete else None
    pnl = value - basis if value is not None else None
    ratio = pnl / basis if pnl is not None and basis > 0 else None
    allocations = tuple(
        PositionAllocation(row, snapshot, snapshot.market_value / value
                           if value is not None and value > 0
                           and snapshot.market_value is not None else None)
        for row, snapshot in zip(rows, snapshots)
    )
    return PortfolioSnapshot(currency, allocations, basis, value, pnl, ratio)
