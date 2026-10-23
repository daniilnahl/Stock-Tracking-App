"""Pure local-only holdings projection under ADR-0019/0020 and FC-051.

Callers supply explicit trusted valuation inputs and bounds. This does not read
stored holdings, establish price provenance, or authorize transmitting holdings
to any LLM. Existing analytics alone supplies the weights; no formula lives here.
"""

from decimal import Decimal
import json

from stock_tracker.domain import Position, PositionValuationInput, Stock, portfolio_snapshot


class ResearchHoldingsValidationError(ValueError):
    """Fixed structural/transport diagnostic without rejected input values."""

    def __init__(self) -> None:
        super().__init__("Research holdings projection is invalid.")


_MISSING = object()


def _positive_limit(value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ResearchHoldingsValidationError()


def _unicode(value: str) -> None:
    index = 0
    while index < len(value):
        point = ord(value[index])
        if 0xD800 <= point <= 0xDBFF:
            if index + 1 >= len(value) or not 0xDC00 <= ord(value[index + 1]) <= 0xDFFF:
                raise ResearchHoldingsValidationError()
            index += 2
        elif 0xDC00 <= point <= 0xDFFF:
            raise ResearchHoldingsValidationError()
        else:
            index += 1


def _copy_input(value: object, byte_cap: int) -> PositionValuationInput:
    if type(value) is not PositionValuationInput:
        raise ResearchHoldingsValidationError()
    position = getattr(value, "position", _MISSING)
    if type(position) is not Position:
        raise ResearchHoldingsValidationError()
    stock = getattr(position, "stock", _MISSING)
    if type(stock) is not Stock:
        raise ResearchHoldingsValidationError()
    symbol = getattr(stock, "symbol", _MISSING)
    exchange = getattr(stock, "exchange", _MISSING)
    if type(symbol) is not str or (exchange is not None and type(exchange) is not str):
        raise ResearchHoldingsValidationError()
    # Canonical JSON needs at least one ASCII byte per input code point. Refuse
    # obviously oversized tickers before scanning or encoding their contents.
    if len(symbol) > byte_cap:
        raise ResearchHoldingsValidationError()
    _unicode(symbol)
    if exchange is not None:
        _unicode(exchange)
    quantity = getattr(position, "quantity", _MISSING)
    cost = getattr(position, "average_cost", _MISSING)
    price = getattr(value, "current_price", _MISSING)
    cost_currency = getattr(value, "cost_currency", _MISSING)
    quote_currency = getattr(value, "quote_currency", _MISSING)
    if type(quantity) is not Decimal or type(cost) is not Decimal:
        raise ResearchHoldingsValidationError()
    if price is not None and type(price) is not Decimal:
        raise ResearchHoldingsValidationError()
    for currency in (cost_currency, quote_currency):
        if currency is not None and type(currency) is not str:
            raise ResearchHoldingsValidationError()
        if currency is not None:
            _unicode(currency)
    # Revalidate required domain values before analytics. Do not inspect or copy
    # Stock.name or unrelated metadata. Copies retain row order and identity
    # components without using equality or ticker-based deduplication.
    copied = Position(Stock(symbol, exchange=exchange), quantity, cost)
    return PositionValuationInput(copied, price, cost_currency, quote_currency)


def project_holdings(
    rows: tuple[PositionValuationInput, ...], *, currency: str,
    max_rows: int, max_output_bytes: int,
) -> bytes:
    """Return exact local ticker/weight JSON, or fail without partial output.

    Structural errors use a fixed safe error. Existing domain currency/value and
    Decimal arithmetic errors remain errors from the accepted domain routines.
    No context, rounding, price or currency convention is added by this helper.
    """
    _positive_limit(max_rows)
    _positive_limit(max_output_bytes)
    if type(rows) is not tuple or len(rows) > max_rows or type(currency) is not str:
        raise ResearchHoldingsValidationError()
    _unicode(currency)
    copied = tuple(_copy_input(row, max_output_bytes) for row in rows)
    snapshot = portfolio_snapshot(copied, currency=currency)
    if snapshot.total_market_value is not None and not snapshot.total_market_value.is_finite():
        raise ResearchHoldingsValidationError()
    for allocation in snapshot.positions:
        weight = allocation.weight
        if weight is not None and (not weight.is_finite() or weight < 0):
            raise ResearchHoldingsValidationError()
    projection = [
        {"ticker": allocation.input.position.stock.symbol,
         "portfolio_weight": None if allocation.weight is None else str(allocation.weight)}
        for allocation in snapshot.positions
    ]
    encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
    chunks = []
    size = 0
    for chunk in encoder.iterencode(projection):
        encoded = chunk.encode("ascii")
        size += len(encoded)
        if size > max_output_bytes:
            raise ResearchHoldingsValidationError()
        chunks.append(encoded)
    return b"".join(chunks)
