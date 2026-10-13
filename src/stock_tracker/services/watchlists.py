"""Local watchlist use cases over a repository and existence-only legacy port."""

from stock_tracker.domain import Position, position_snapshot
from stock_tracker.exceptions import LegacyStatePresentError, PersistenceValidationError
from stock_tracker.persistence.models import WatchlistRecord
from stock_tracker.persistence.protocols import WatchlistRepository

from .models import EntryView, WatchlistView, validated_record
from .protocols import LegacyPresence


class WatchlistService:
    """Preserve one explicit namespace without configuration or concrete IO."""

    def __init__(
        self, repository: WatchlistRepository, *, namespace: str, legacy_present: LegacyPresence,
    ) -> None:
        validated_record(WatchlistRecord(namespace, "Watchlist", ()))
        if not callable(legacy_present):
            raise PersistenceValidationError()
        self._repository = repository
        self._namespace = namespace
        self._legacy_present = legacy_present

    def _candidate(self, record: WatchlistRecord) -> WatchlistRecord:
        candidate = validated_record(record)
        if candidate.namespace != self._namespace:
            raise PersistenceValidationError()
        return candidate

    def _require_no_legacy(self) -> None:
        present = self._legacy_present()
        if type(present) is not bool:
            raise PersistenceValidationError()
        if present:
            raise LegacyStatePresentError()

    def load(self) -> WatchlistRecord:
        record = self._repository.get(self._namespace)
        if record is not None:
            return self._candidate(record)
        self._require_no_legacy()
        return WatchlistRecord(self._namespace, "Watchlist", ())

    def save(self, record: WatchlistRecord) -> None:
        candidate = self._candidate(record)
        existing = self._repository.get(self._namespace)
        if existing is None:
            self._require_no_legacy()
        else:
            self._candidate(existing)
        self._repository.save(candidate)

    def view(self, record: WatchlistRecord) -> WatchlistView:
        candidate = self._candidate(record)
        entries = tuple(EntryView(entry, None if entry.average_cost is None else position_snapshot(
            Position(entry.stock, entry.quantity, entry.average_cost), entry.current_price,
        )) for entry in candidate.entries)
        return WatchlistView(candidate, entries)

    def remove(self, record: WatchlistRecord, symbol: str) -> WatchlistRecord:
        candidate = self._candidate(record)
        if not isinstance(symbol, str):
            raise PersistenceValidationError()
        entries = list(candidate.entries)
        # Legacy Stock facades compare by object identity. Delete the selected
        # ordinal rather than a first equal dataclass row; retain forward skips.
        index = 0
        while index < len(entries):
            if entries[index].stock.symbol == symbol:
                del entries[index]
            index += 1
        return WatchlistRecord(candidate.namespace, candidate.name, tuple(entries))
