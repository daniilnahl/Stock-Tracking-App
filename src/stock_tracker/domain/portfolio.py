"""Portfolio identity with an independent, ordered collection of positions."""

from dataclasses import dataclass

from .errors import DomainValidationError
from .position import Position


@dataclass(init=False)
class Portfolio:
    """Own a mutable position list without persistence or analytics behavior."""

    id: int | None
    name: str
    positions: list[Position]

    def __init__(
        self, id: int | None, name: str, positions: list[Position] | None = None,
    ) -> None:
        if id is not None and (isinstance(id, bool) or not isinstance(id, int)):
            raise DomainValidationError("id must be an int or None.")
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            raise DomainValidationError(
                "name must be a nonblank string without surrounding whitespace."
            )
        if positions is not None and not isinstance(positions, list):
            raise DomainValidationError("positions must be a list of Position instances or None.")
        owned_positions = [] if positions is None else list(positions)
        if any(not isinstance(position, Position) for position in owned_positions):
            raise DomainValidationError("positions must contain only Position instances.")
        self.id = id
        self.name = name
        self.positions = owned_positions
