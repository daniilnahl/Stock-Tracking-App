"""Neutral application results shared by the accepted M6 service contracts."""

from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal
from typing import Literal

from stock_tracker.domain import DomainValidationError, PositionSnapshot, Stock
from stock_tracker.exceptions import PersistenceValidationError, ProviderResponseError
from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord
from stock_tracker.providers.models import CompanyProfile, PeriodChanges, PriceBar


def validated_record(record: WatchlistRecord) -> WatchlistRecord:
    """Revalidate complete input without changing unresolved security identities."""
    if not isinstance(record, WatchlistRecord) or not isinstance(getattr(record, "entries", None), tuple):
        raise PersistenceValidationError()
    entries = []
    try:
        for entry in record.entries:
            if not isinstance(entry, WatchlistEntry) or not isinstance(getattr(entry, "stock", None), Stock):
                raise PersistenceValidationError()
            stock = entry.stock
            Stock(*(getattr(stock, field, object()) for field in ("symbol", "name", "exchange")))
            # Keep the original security identity, including unresolved exchange.
            entries.append(WatchlistEntry(
                stock, *(getattr(entry, field.name, object()) for field in fields(WatchlistEntry)[1:]),
            ))
        candidate = WatchlistRecord(getattr(record, "namespace", None),
                                   getattr(record, "name", None), tuple(entries))
        for value in (candidate.namespace, candidate.name):
            value.encode("utf-8")
        for entry in candidate.entries:
            for value in (entry.stock.symbol, entry.stock.name, entry.stock.exchange,
                          *(getattr(entry, field.name) for field in fields(WatchlistEntry)[4:])):
                if isinstance(value, str):
                    value.encode("utf-8")
        return candidate
    except (DomainValidationError, UnicodeEncodeError):
        raise PersistenceValidationError() from None


@dataclass(frozen=True, slots=True)
class EntryView:
    entry: WatchlistEntry
    snapshot: PositionSnapshot | None


@dataclass(frozen=True, slots=True)
class WatchlistView:
    record: WatchlistRecord
    entries: tuple[EntryView, ...]


@dataclass(frozen=True, slots=True)
class AddPreparation:
    status: Literal["ready", "invalid", "duplicate"]
    profile: CompanyProfile | None
    periods: PeriodChanges | None

    def __post_init__(self) -> None:
        if self.status == "ready":
            if not isinstance(self.profile, CompanyProfile) or not isinstance(self.periods, PeriodChanges):
                raise ProviderResponseError()
            self.profile.__post_init__()
            self.periods.__post_init__()
            if self.profile.symbol != self.periods.symbol:
                raise ProviderResponseError(field="symbol")
        elif self.status not in ("invalid", "duplicate") or self.profile is not None or self.periods is not None:
            raise ProviderResponseError()


@dataclass(frozen=True, slots=True)
class OwnershipInput:
    quantity: Decimal
    average_cost: Decimal | None

    def __post_init__(self) -> None:
        for field in ("quantity", "average_cost"):
            value = getattr(self, field)
            if field == "average_cost" and value is None and self.quantity == 0:
                continue
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise DomainValidationError(f"{field} must be a finite nonnegative Decimal.")


@dataclass(frozen=True, slots=True)
class EntryUpdate:
    ordinal: int
    entry: WatchlistEntry
    profile: CompanyProfile | None
    periods: PeriodChanges | None
    invalidate_periods: bool

    def __post_init__(self) -> None:
        if type(self.ordinal) is not int or self.ordinal < 0 or type(self.invalidate_periods) is not bool:
            raise PersistenceValidationError()
        validated_record(WatchlistRecord("validation", "validation", (self.entry,)))
        if self.invalidate_periods and self.periods is not None:
            raise ProviderResponseError()
        for model, expected in ((self.profile, CompanyProfile), (self.periods, PeriodChanges)):
            if model is not None:
                if not isinstance(model, expected):
                    raise ProviderResponseError()
                model.__post_init__()
                if model.symbol != self.entry.stock.symbol.strip().upper():
                    raise ProviderResponseError(field="symbol")


@dataclass(frozen=True, slots=True)
class PreparedWatchlist:
    record: WatchlistRecord
    updates: tuple[EntryUpdate, ...]

    def __post_init__(self) -> None:
        record = validated_record(self.record)
        if not isinstance(self.updates, tuple):
            raise PersistenceValidationError()
        for update in self.updates:
            if not isinstance(update, EntryUpdate):
                raise PersistenceValidationError()
            update.__post_init__()
            if update.ordinal >= len(record.entries) or (
                update.entry.stock.symbol != record.entries[update.ordinal].stock.symbol
            ):
                raise PersistenceValidationError()


@dataclass(frozen=True, slots=True)
class HistoryView:
    stock: Stock
    start: date
    end: date
    bars: tuple[PriceBar, ...]
