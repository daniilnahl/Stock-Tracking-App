"""Current-data orchestration over injected capabilities, without UI or saves."""

from collections.abc import Callable
from dataclasses import fields, replace

from stock_tracker.domain import DomainValidationError, Position, Stock, position_snapshot
from stock_tracker.exceptions import InvalidTickerError, PersistenceValidationError, ProviderResponseError, StockTrackerError
from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord
from stock_tracker.providers.models import CompanyProfile, InstrumentIdentity, PeriodChanges

from .models import AddPreparation, EntryUpdate, OwnershipInput, PreparedWatchlist, validated_record
from .numeric import to_decimal
from .protocols import CurrentProviderSource


def _known(value: str | None) -> str | None:
    return None if value in (None, "N/A") else value


def _model(value, expected):
    if not isinstance(value, expected):
        raise ProviderResponseError()
    return expected(*(getattr(value, field.name, object()) for field in fields(expected)))


def _profile(provider, symbol: str) -> CompanyProfile:
    profile = _model(provider.get_company_profile(symbol), CompanyProfile)
    if profile.symbol != symbol.strip().upper():
        raise ProviderResponseError(field="symbol")
    return profile


def _periods(provider, symbol: str) -> PeriodChanges:
    periods = _model(provider.get_period_changes(symbol), PeriodChanges)
    if periods.symbol != symbol.strip().upper():
        raise ProviderResponseError(field="symbol")
    return periods


def _profile_entry(entry: WatchlistEntry, profile: CompanyProfile) -> WatchlistEntry:
    metadata = {}
    for field, existing in (("exchange", entry.stock.exchange), ("currency", entry.currency)):
        existing, returned = _known(existing), getattr(profile, field)
        if existing is not None and returned is not None and existing != returned:
            raise ProviderResponseError(field=field)
        metadata[field] = returned if returned is not None else existing
    stock = Stock(entry.stock.symbol, _known(profile.name), _known(metadata["exchange"]))
    candidate = replace(entry, stock=stock, current_price=profile.price,
                        currency=metadata["currency"] or "N/A", sector=profile.sector or "N/A",
                        country=profile.country or "N/A")
    if candidate.average_cost is not None:
        position_snapshot(Position(stock, candidate.quantity, candidate.average_cost), candidate.current_price)
    return candidate


class CurrentDataService:
    """Prepare candidates and publish neutral progress; persistence is caller-owned."""

    def __init__(self, providers: CurrentProviderSource) -> None:
        if not callable(providers):
            raise PersistenceValidationError()
        self._providers = providers

    def prepare_add(self, record: WatchlistRecord, symbol: str) -> AddPreparation:
        candidate = validated_record(record)
        try:
            provider = self._providers("resolve", None, on_configuration_failure=None)
            identity = provider.resolve_symbol(symbol)
        except InvalidTickerError:
            return AddPreparation("invalid", None, None)
        identity = _model(identity, InstrumentIdentity)
        if not isinstance(symbol, str) or identity.symbol != symbol.strip().upper() or identity.exchange != "NASDAQ":
            raise ProviderResponseError(field="symbol")
        if any(entry.stock.symbol == symbol for entry in candidate.entries):
            return AddPreparation("duplicate", None, None)
        # Preserve the legacy constructor's local identity validation after lookup.
        Stock(symbol)
        profile = _profile(self._providers("profile", None, on_configuration_failure=None), symbol)
        periods = _periods(self._providers("periods", None, on_configuration_failure=None), symbol)
        return AddPreparation("ready", profile, periods)

    def validate_ownership(self, quantity: str, average_cost: str) -> OwnershipInput:
        for field, value in (("amount_owned", quantity), ("cost_basis", average_cost)):
            if not isinstance(value, str):
                raise DomainValidationError(f"{field} must be a finite plain decimal number.")
        parsed_quantity = to_decimal(quantity, "amount_owned")
        parsed_cost = None if parsed_quantity == 0 and average_cost == "-" else to_decimal(average_cost, "cost_basis")
        return OwnershipInput(parsed_quantity, parsed_cost)

    def finish_add(
        self, record: WatchlistRecord, prepared: AddPreparation, ownership: OwnershipInput,
    ) -> PreparedWatchlist:
        candidate = validated_record(record)
        if not isinstance(prepared, AddPreparation) or not isinstance(ownership, OwnershipInput):
            raise PersistenceValidationError()
        if getattr(prepared, "status", None) != "ready":
            raise PersistenceValidationError()
        prepared = AddPreparation("ready", _model(getattr(prepared, "profile", None), CompanyProfile),
                                  _model(getattr(prepared, "periods", None), PeriodChanges))
        ownership = OwnershipInput(getattr(ownership, "quantity", object()),
                                   getattr(ownership, "average_cost", object()))
        profile = prepared.profile
        entry = WatchlistEntry(Stock(profile.symbol), ownership.quantity, ownership.average_cost,
                              None, *("N/A" for _ in range(12)))
        entry = _profile_entry(entry, profile)
        ordinal = len(candidate.entries)
        result = WatchlistRecord(candidate.namespace, candidate.name, (*candidate.entries, entry))
        update = EntryUpdate(ordinal, entry, profile, prepared.periods, False)
        return PreparedWatchlist(result, (update,))

    def refresh(
        self, record: WatchlistRecord, *, on_update: Callable[[EntryUpdate], None],
    ) -> PreparedWatchlist:
        candidate = validated_record(record)
        if not callable(on_update):
            raise PersistenceValidationError()
        entries, updates = list(candidate.entries), []
        for ordinal, original in enumerate(candidate.entries):
            profile_invalidated = False
            def profile_failure():
                nonlocal profile_invalidated
                profile_invalidated = True
                on_update(EntryUpdate(ordinal, replace(original, current_price=None), None, None, False))
            try:
                provider = self._providers("profile", ordinal, on_configuration_failure=profile_failure)
                profile = _profile(provider, original.stock.symbol)
                current = _profile_entry(original, profile)
                profile_update = EntryUpdate(ordinal, current, profile, None, False)
            except StockTrackerError:
                if not profile_invalidated:
                    profile_failure()
                raise
            on_update(profile_update)
            updates.append(profile_update)

            periods_invalidated = False
            def periods_failure():
                nonlocal periods_invalidated
                periods_invalidated = True
                on_update(EntryUpdate(ordinal, current, None, None, True))
            try:
                provider = self._providers("periods", ordinal, on_configuration_failure=periods_failure)
                periods = _periods(provider, original.stock.symbol)
                periods_update = EntryUpdate(ordinal, current, None, periods, False)
            except StockTrackerError:
                if not periods_invalidated:
                    periods_failure()
                raise
            on_update(periods_update)
            updates.append(periods_update)
            entries[ordinal] = current
        result = WatchlistRecord(candidate.namespace, candidate.name, tuple(entries))
        return PreparedWatchlist(result, tuple(updates))
