"""Pure prepared-criteria validation and binding under ADR-0018/0019.

These records describe user intent, not evaluated facts or executable instructions.
Nothing here loads configuration, filters private content, starts research, or
establishes permission to transmit the input. Callers supply their own byte cap.
"""

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Literal


class ResearchCriteriaValidationError(ValueError):
    """A fixed diagnostic that never incorporates the rejected input."""

    def __init__(self) -> None:
        super().__init__("Research criteria are invalid.")


_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:[.][0-9]+)?", re.ASCII)
_CONTROLS = re.compile(r"[\x00-\x1f\x7f-\x9f]")
# ECMAScript trim, used only to test blankness; entered strings are never trimmed.
_WHITESPACE = (
    "\u0009\u000a\u000b\u000c\u000d\u0020\u00a0\u1680"
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007"
    "\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
)
_INVALID = object()


def _unicode_units(value: object) -> int:
    if type(value) is not str:
        raise ResearchCriteriaValidationError()
    count = index = 0
    while index < len(value):
        point = ord(value[index])
        if 0xD800 <= point <= 0xDBFF:
            if index + 1 >= len(value) or not 0xDC00 <= ord(value[index + 1]) <= 0xDFFF:
                raise ResearchCriteriaValidationError()
            count += 2
            index += 2
        elif 0xDC00 <= point <= 0xDFFF:
            raise ResearchCriteriaValidationError()
        else:
            count += 2 if point > 0xFFFF else 1
            index += 1
    return count


def _text(value: object, limit: int) -> None:
    units = _unicode_units(value)
    if units > limit or not value.strip(_WHITESPACE) or _CONTROLS.search(value):
        raise ResearchCriteriaValidationError()


def _endpoint(value: object) -> None:
    if value is None:
        return
    if type(value) is not str or len(value) > 128 or _DECIMAL.fullmatch(value) is None:
        raise ResearchCriteriaValidationError()


def _decimal_parts(value: str) -> tuple[bool, str, str]:
    unsigned = value[1:] if value.startswith("-") else value
    integer, _, fraction = unsigned.partition(".")
    zero = integer == "0" and all(digit == "0" for digit in fraction)
    return value.startswith("-") and not zero, integer, fraction


def _compare(first: str, second: str) -> int:
    """Compare validated decimal strings exactly, without numeric conversion."""
    negative_a, integer_a, fraction_a = _decimal_parts(first)
    negative_b, integer_b, fraction_b = _decimal_parts(second)
    if negative_a != negative_b:
        return -1 if negative_a else 1
    width = max(len(fraction_a), len(fraction_b))
    magnitude_a = (len(integer_a), integer_a, fraction_a.ljust(width, "0"))
    magnitude_b = (len(integer_b), integer_b, fraction_b.ljust(width, "0"))
    magnitude = (magnitude_a > magnitude_b) - (magnitude_a < magnitude_b)
    return -magnitude if negative_a else magnitude


def _range(parameter: object, unit: object, minimum: object, maximum: object) -> None:
    _text(parameter, 80)
    _text(unit, 80)
    _endpoint(minimum)
    _endpoint(maximum)
    if minimum is None and maximum is None:
        raise ResearchCriteriaValidationError()
    if minimum is not None and maximum is not None and _compare(minimum, maximum) > 0:
        raise ResearchCriteriaValidationError()


@dataclass(frozen=True, slots=True)
class RangeCriterion:
    parameter: str
    unit: str
    minimum: str | None
    maximum: str | None

    def __post_init__(self) -> None:
        _range(self.parameter, self.unit, self.minimum, self.maximum)


@dataclass(frozen=True, slots=True)
class TextCriterion:
    parameter: str
    value: str

    def __post_init__(self) -> None:
        _text(self.parameter, 80)
        _text(self.value, 256)


@dataclass(frozen=True, slots=True)
class PreparedCriteria:
    match: Literal["all", "any"]
    criteria: tuple[RangeCriterion | TextCriterion, ...]

    def __post_init__(self) -> None:
        _model(self)


def _match(value: object) -> None:
    if type(value) is not str or value not in ("all", "any"):
        raise ResearchCriteriaValidationError()


def _model(snapshot: object) -> None:
    if type(snapshot) is not PreparedCriteria:
        raise ResearchCriteriaValidationError()
    _match(getattr(snapshot, "match", None))
    rows = getattr(snapshot, "criteria", None)
    if type(rows) is not tuple or not 1 <= len(rows) <= 20:
        raise ResearchCriteriaValidationError()
    for row in rows:
        if type(row) is RangeCriterion:
            _range(*(getattr(row, field, _INVALID)
                     for field in ("parameter", "unit", "minimum", "maximum")))
        elif type(row) is TextCriterion:
            _text(getattr(row, "parameter", None), 80)
            _text(getattr(row, "value", None), 256)
        else:
            raise ResearchCriteriaValidationError()


def _keys(value: object, keys: tuple[str, ...]) -> None:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ResearchCriteriaValidationError()
    if set(value) != set(keys):
        raise ResearchCriteriaValidationError()


def validate_prepared_criteria(value: object) -> PreparedCriteria:
    """Validate a prepared JSON-shaped object, copying it into immutable records."""
    _keys(value, ("schema_version", "kind", "match", "criteria"))
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ResearchCriteriaValidationError()
    if type(value["kind"]) is not str or value["kind"] != "user_stock_criteria":
        raise ResearchCriteriaValidationError()
    _match(value["match"])
    incoming = value["criteria"]
    if type(incoming) is not list or not 1 <= len(incoming) <= 20:
        raise ResearchCriteriaValidationError()
    rows = []
    for row in incoming:
        if type(row) is not dict or any(type(key) is not str for key in row):
            raise ResearchCriteriaValidationError()
        kind = row.get("kind")
        if type(kind) is not str:
            raise ResearchCriteriaValidationError()
        if kind == "range":
            _keys(row, ("parameter", "kind", "unit", "minimum", "maximum"))
            rows.append(RangeCriterion(row["parameter"], row["unit"],
                                       row["minimum"], row["maximum"]))
        elif kind == "text":
            _keys(row, ("parameter", "kind", "value"))
            rows.append(TextCriterion(row["parameter"], row["value"]))
        else:
            raise ResearchCriteriaValidationError()
    return PreparedCriteria(value["match"], tuple(rows))


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResearchCriteriaValidationError()
        result[key] = value
    return result


def _reject_number(token: str) -> None:
    raise ResearchCriteriaValidationError()


def parse_prepared_criteria(payload: bytes, *, max_bytes: int) -> PreparedCriteria:
    """Read strict UTF-8 JSON within an explicit caller bound; never read a file."""
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ResearchCriteriaValidationError()
    if type(payload) is not bytes or len(payload) > max_bytes:
        raise ResearchCriteriaValidationError()
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_float=_reject_number, parse_constant=_reject_number)
    except (ValueError, UnicodeError, RecursionError):
        value = _INVALID
    # Raise outside the handler so the rejected JSON/Unicode exception is not
    # retained as an implicit cause carrying private payload or decoder details.
    if value is _INVALID:
        raise ResearchCriteriaValidationError()
    return validate_prepared_criteria(value)


def canonical_criteria_bytes(snapshot: PreparedCriteria) -> bytes:
    """Serialize revalidated records with the exact ADR-0019 canonical encoding."""
    _model(snapshot)
    rows = []
    for row in snapshot.criteria:
        if type(row) is RangeCriterion:
            rows.append({"parameter": row.parameter, "kind": "range", "unit": row.unit,
                         "minimum": row.minimum, "maximum": row.maximum})
        else:
            rows.append({"parameter": row.parameter, "kind": "text", "value": row.value})
    value = {"schema_version": 1, "kind": "user_stock_criteria",
             "match": snapshot.match, "criteria": rows}
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def criteria_sha256(snapshot: PreparedCriteria) -> str:
    """Bind the canonical criteria bytes, without claiming evidence or consent."""
    return hashlib.sha256(canonical_criteria_bytes(snapshot)).hexdigest()
