"""Projection and rendering of neutral application results at the CLI boundary."""

from dataclasses import replace
from types import SimpleNamespace

from watch_list import Watch_list
from stock_tracker.compatibility import presentation as legacy
from stock_tracker.exceptions import PersistenceValidationError
from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord
from stock_tracker.services.models import EntryUpdate, HistoryView, PreparedWatchlist, WatchlistView, validated_record


PERIOD_FIELDS = ("price_1d", "price_5d", "price_30d", "price_3m", "price_6m",
                 "price_1y", "price_3y", "price_5y")
PROVIDER_PERIODS = ("day_1", "day_5", "month_1", "month_3", "month_6", "year_1", "year_3", "year_5")


def apply_entry_update(entry: WatchlistEntry, update: EntryUpdate) -> WatchlistEntry:
    if not isinstance(entry, WatchlistEntry) or not isinstance(update, EntryUpdate):
        raise PersistenceValidationError()
    EntryUpdate.__post_init__(update)
    if entry.stock.symbol != update.entry.stock.symbol:
        raise PersistenceValidationError()
    display = {field: getattr(entry, field) for field in ("market_cap", *PERIOD_FIELDS)}
    if update.profile is not None:
        cap = update.profile.market_cap
        display["market_cap"] = "N/A" if cap is None else legacy.format_mcap(cap)
    if update.periods is not None:
        for target, source in zip(PERIOD_FIELDS, PROVIDER_PERIODS):
            value = getattr(update.periods, source)
            display[target] = "N/A" if value is None else format(value, ".2f").rstrip("0").rstrip(".")
    if update.invalidate_periods:
        display.update({field: "N/A" for field in PERIOD_FIELDS})
    return replace(update.entry, **display)


def project_prepared(result: PreparedWatchlist) -> WatchlistRecord:
    if not isinstance(result, PreparedWatchlist):
        raise PersistenceValidationError()
    PreparedWatchlist.__post_init__(result)
    entries = list(result.record.entries)
    for update in result.updates:
        entries[update.ordinal] = apply_entry_update(entries[update.ordinal], update)
    return validated_record(WatchlistRecord(result.record.namespace, result.record.name, tuple(entries)))


def render_watchlist(view: WatchlistView) -> None:
    # Reuse the existing escaped Rich table without constructing mutable facades
    # or obtaining provider data. Snapshot ratios are formatted only here.
    rows = []
    for item in view.entries:
        entry, snapshot = item.entry, item.snapshot
        rows.append(SimpleNamespace(
            ticker_symbol=entry.stock.symbol, name=entry.stock.name, exchange=entry.stock.exchange,
            amount_owned=str(entry.quantity), cost_basis="-" if entry.average_cost is None else str(entry.average_cost),
            current_price=None if entry.current_price is None else str(entry.current_price),
            total_return=legacy.format_return(None if snapshot is None else snapshot.unrealized_return),
            **{field: getattr(entry, field) for field in ("sector", "country", "market_cap", *PERIOD_FIELDS)},
        ))
    Watch_list(view.record.name, rows).show_stocks()


def render_history(view: HistoryView) -> None:
    legacy.render_history(view)
