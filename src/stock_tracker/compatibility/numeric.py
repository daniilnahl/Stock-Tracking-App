"""Explicit numeric conversion at legacy/provider/user-input boundaries."""

from decimal import Decimal, InvalidOperation
import re

from stock_tracker.domain import DomainValidationError


_PLAIN_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def to_decimal(value: Decimal | str | int | float, field: str) -> Decimal:
    """Preserve decimal input; legacy floats retain only their decimal spelling."""
    message = f"{field} must be a finite plain decimal number."
    if isinstance(value, bool):
        raise DomainValidationError(message)
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, str):
        text = value.strip()
        if _PLAIN_DECIMAL.fullmatch(text) is None:
            raise DomainValidationError(message)
        try:
            result = Decimal(text)
        except InvalidOperation:
            raise DomainValidationError(message) from None
    elif isinstance(value, (int, float)):
        result = Decimal(str(value))
    else:
        raise DomainValidationError(message)
    if not result.is_finite():
        raise DomainValidationError(message)
    return result
