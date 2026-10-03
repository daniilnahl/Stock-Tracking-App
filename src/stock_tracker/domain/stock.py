"""Immutable security identity without portfolio or infrastructure state."""

from dataclasses import dataclass

from .errors import DomainValidationError


@dataclass(frozen=True, eq=False, slots=True)
class Stock:
    """Identify a security by its exact symbol and known exchange, if supplied."""

    symbol: str
    name: str | None = None
    exchange: str | None = None

    def __post_init__(self) -> None:
        for field, value, optional in (
            ("symbol", self.symbol, False),
            ("name", self.name, True),
            ("exchange", self.exchange, True),
        ):
            if optional and value is None:
                continue
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise DomainValidationError(
                    f"{field} must be a nonblank string without surrounding whitespace."
                )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Stock):
            return NotImplemented
        if self is other:
            return True
        if self.exchange is None or other.exchange is None:
            return False
        return (self.symbol, self.exchange) == (other.symbol, other.exchange)

    def __hash__(self) -> int:
        if self.exchange is None:
            return object.__hash__(self)
        return hash((self.symbol, self.exchange))
