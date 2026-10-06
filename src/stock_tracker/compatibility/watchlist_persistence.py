"""Explicit facade/record mapping; credentials are supplied only at restoration."""

from dataclasses import fields

from stock import Stock as LegacyStock
from watch_list import Watch_list
from stock_tracker.domain import DomainValidationError, Stock
from stock_tracker.exceptions import PersistenceValidationError
from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord

from .numeric import to_decimal


_METADATA = tuple(field.name for field in fields(WatchlistEntry))[4:]


def watchlist_to_record(watchlist: Watch_list, namespace: str) -> WatchlistRecord:
    """Capture authoritative inputs and display metadata, never clients/keys/returns."""
    if not isinstance(watchlist, Watch_list) or not isinstance(getattr(watchlist, "stocks", None), list):
        raise PersistenceValidationError()
    entries = []
    try:
        for facade in watchlist.stocks:
            if not isinstance(facade, LegacyStock):
                raise PersistenceValidationError()
            identity = Stock(
                getattr(facade, "ticker_symbol", None),
                None if (name := getattr(facade, "name", object())) in (None, "N/A") else name,
                None if (exchange := getattr(facade, "exchange", object())) in (None, "N/A") else exchange,
            )
            quantity = to_decimal(getattr(facade, "amount_owned", None), "quantity")
            cost_text = getattr(facade, "cost_basis", None)
            cost = None if cost_text == "-" else to_decimal(cost_text, "average_cost")
            price_text = getattr(facade, "current_price", object())
            quote = None if price_text in (None, "N/A") else to_decimal(price_text, "current_price")
            entries.append(WatchlistEntry(identity, quantity, cost, quote,
                                         *(getattr(facade, field, object()) for field in _METADATA)))
        return WatchlistRecord(namespace, getattr(watchlist, "name", None), tuple(entries))
    except (DomainValidationError, PersistenceValidationError):
        raise PersistenceValidationError() from None


def record_to_watchlist(record: WatchlistRecord, runtime_key: str | None) -> Watch_list:
    """Restore offline with the explicitly supplied current key and recomputed snapshots."""
    if runtime_key is not None and not isinstance(runtime_key, str):
        raise PersistenceValidationError()
    if not isinstance(record, WatchlistRecord):
        raise PersistenceValidationError()
    try:
        # Revalidate mutated frozen fields without depending on concrete storage.
        source = WatchlistRecord(getattr(record, "namespace", None), getattr(record, "name", None),
                                 getattr(record, "entries", None))
        entries = []
        for entry in source.entries:
            stock = getattr(entry, "stock", None)
            if not isinstance(stock, Stock):
                raise PersistenceValidationError()
            identity = Stock(*(getattr(stock, field, object()) for field in ("symbol", "name", "exchange")))
            entries.append(WatchlistEntry(identity, *(getattr(entry, field.name, object())
                                                      for field in fields(WatchlistEntry)[1:])))
        candidate = WatchlistRecord(source.namespace, source.name, tuple(entries))
    except (DomainValidationError, PersistenceValidationError):
        raise PersistenceValidationError() from None
    return Watch_list(candidate.name, [LegacyStock(
        entry.stock.symbol, runtime_key, name=entry.stock.name, exchange=entry.stock.exchange,
        amount_owned=str(entry.quantity),
        cost_basis="-" if entry.average_cost is None else str(entry.average_cost),
        current_price=None if entry.current_price is None else str(entry.current_price),
        **{field: getattr(entry, field) for field in _METADATA},
    ) for entry in candidate.entries])
