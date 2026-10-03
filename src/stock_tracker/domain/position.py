"""Immutable ownership inputs for a security."""

from dataclasses import dataclass
from decimal import Decimal

from .errors import DomainValidationError
from .stock import Stock


@dataclass(frozen=True, slots=True)
class Position:
    """Hold fractional shares and an authoritative average cost per share."""

    stock: Stock
    quantity: Decimal
    average_cost: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.stock, Stock):
            raise DomainValidationError("stock must be a Stock.")
        for field, value in (
            ("quantity", self.quantity),
            ("average_cost", self.average_cost),
        ):
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise DomainValidationError(f"{field} must be a finite nonnegative Decimal.")

    def with_owned_data(self, quantity: Decimal, average_cost: Decimal) -> "Position":
        """Return validated replacement inputs without changing this position."""
        return Position(self.stock, quantity, average_cost)
