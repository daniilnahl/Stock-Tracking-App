"""Pure position snapshot calculations defined by FC-020/030/040/041."""

from dataclasses import dataclass
from decimal import Decimal

from .errors import DomainValidationError
from .position import Position


@dataclass(frozen=True, slots=True)
class PositionSnapshot:
    """Currency amounts and a dimensionless unrealized-return ratio.

    None denotes unavailable valuation or an undefined zero-basis return.
    """

    cost_basis: Decimal
    market_value: Decimal | None
    unrealized_pnl: Decimal | None
    unrealized_return: Decimal | None


def position_snapshot(position: Position, current_price: Decimal | None) -> PositionSnapshot:
    """Value a position using an explicit same-currency per-share quote.

    Arithmetic uses the caller's Decimal context without extra quantization.
    A missing quote remains unavailable, even for zero quantity.
    """
    if not isinstance(position, Position):
        raise DomainValidationError("position must be a Position.")
    if current_price is not None and (
        not isinstance(current_price, Decimal)
        or not current_price.is_finite()
        or current_price < 0
    ):
        raise DomainValidationError("current_price must be a finite nonnegative Decimal or None.")

    cost_basis = position.quantity * position.average_cost
    if current_price is None:
        return PositionSnapshot(cost_basis, None, None, None)

    market_value = position.quantity * current_price
    unrealized_pnl = market_value - cost_basis
    unrealized_return = unrealized_pnl / cost_basis if cost_basis > 0 else None
    return PositionSnapshot(cost_basis, market_value, unrealized_pnl, unrealized_return)
