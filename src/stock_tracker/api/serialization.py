"""Explicit projections of already computed neutral results; no arithmetic."""

from datetime import date
from decimal import Decimal

from stock_tracker.domain import DomainValidationError, PositionSnapshot, Stock
from stock_tracker.exceptions import MarketDataUnavailableError, ProviderResponseError
from stock_tracker.services.history_policy import validated_raw_bars
from stock_tracker.services.models import HistoryView, WatchlistView, validated_record

from .context import ApiServices
from .errors import ApiFailure


METADATA_FIELDS = (
    "sector", "country", "currency", "market_cap", "price_1d", "price_5d",
    "price_30d", "price_3m", "price_6m", "price_1y", "price_3y", "price_5y",
)
SNAPSHOT_FIELDS = ("cost_basis", "market_value", "unrealized_pnl", "unrealized_return")


def decimal_text(value):
    if value is None:
        return None
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ApiFailure("internal_error")
    return str(value)


def stock_payload(stock: Stock):
    if not isinstance(stock, Stock):
        raise ApiFailure("internal_error")
    try:
        Stock.__post_init__(stock)
    except DomainValidationError:
        raise ApiFailure("internal_error") from None
    return {"symbol": stock.symbol, "name": stock.name, "exchange": stock.exchange}


def watchlist_payload(view: WatchlistView):
    if not isinstance(view, WatchlistView):
        raise ApiFailure("internal_error")
    record = validated_record(view.record)
    if not isinstance(view.entries, tuple) or len(view.entries) != len(record.entries):
        raise ApiFailure("internal_error")
    if record.namespace not in ("menu_watchlist", "daniils_stock_method"):
        raise ApiFailure("internal_error")
    rows = []
    for ordinal, (entry, row) in enumerate(zip(record.entries, view.entries)):
        # Validate row association without using Stock equality, which deliberately
        # treats unresolved identity differently from stored ordinal association.
        if row.entry is not view.record.entries[ordinal]:
            raise ApiFailure("internal_error")
        snapshot = row.snapshot
        if (snapshot is None) != (entry.average_cost is None) or (
            snapshot is not None and not isinstance(snapshot, PositionSnapshot)
        ):
            raise ApiFailure("internal_error")
        if snapshot is not None:
            if (not isinstance(snapshot.cost_basis, Decimal) or not snapshot.cost_basis.is_finite()
                    or snapshot.cost_basis < 0 or
                    (snapshot.market_value is None and (snapshot.unrealized_pnl is not None or snapshot.unrealized_return is not None)) or
                    (snapshot.market_value is not None and snapshot.unrealized_pnl is None) or
                    (snapshot.cost_basis == 0 and snapshot.unrealized_return is not None) or
                    (snapshot.cost_basis > 0 and snapshot.market_value is not None and snapshot.unrealized_return is None)):
                raise ApiFailure("internal_error")
            if snapshot.market_value is not None and (
                not isinstance(snapshot.market_value, Decimal) or not snapshot.market_value.is_finite() or snapshot.market_value < 0
            ):
                raise ApiFailure("internal_error")
        rows.append({
            "ordinal": ordinal, "stock": stock_payload(entry.stock),
            "quantity": decimal_text(entry.quantity), "average_cost": decimal_text(entry.average_cost),
            "current_price": decimal_text(entry.current_price),
            "metadata": {field: getattr(entry, field) for field in METADATA_FIELDS},
            "snapshot": None if snapshot is None else {
                field: decimal_text(getattr(snapshot, field)) for field in SNAPSHOT_FIELDS
            },
        })
    return {"namespace": record.namespace, "name": record.name, "observation": "saved",
            "provenance": {"source": None, "observed_at": None, "retrieved_at": None, "freshness": "unknown"},
            "entries": rows}


def history_payload(view: HistoryView, *, ordinal: int, services: ApiServices):
    if (not isinstance(view, HistoryView) or type(ordinal) is not int or ordinal < 0
            or type(view.start) is not date or type(view.end) is not date):
        raise ApiFailure("internal_error")
    identity = stock_payload(view.stock)
    if not isinstance(view.bars, tuple) or view.start > view.end:
        raise ApiFailure("internal_error")
    try:
        bars = validated_raw_bars(list(view.bars), view.stock.symbol.upper(), view.start, view.end)
    except (ProviderResponseError, MarketDataUnavailableError):
        raise ApiFailure("internal_error") from None
    return {
        "stock": identity, "ordinal": ordinal,
        "start": view.start.isoformat(), "end": view.end.isoformat(), "price_basis": "raw",
        "provenance": {"source": services.history_source, "observed_at": None, "retrieved_at": None,
                       "currency": None, "freshness": "accepted_cache_policy" if services.history_cache_policy else "unknown"},
        "bars": [{"symbol": bar.symbol, "date": bar.date.isoformat(),
                  "open": decimal_text(bar.open), "high": decimal_text(bar.high),
                  "low": decimal_text(bar.low), "close": decimal_text(bar.close),
                  "adjusted_close": None, "volume": bar.volume} for bar in bars],
    }
