"""Bounded neutral history sidecar; independent of holdings and SQLite."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from stock_tracker.exceptions import HistoryCacheError, ProviderResponseError
from stock_tracker.providers.models import HistoryObservation, PriceBar, _symbol

MAX_BYTES = 16 * 1024 * 1024
MAX_ENTRIES = 32
MAX_BARS = 3660
MAX_STRING = 4096
TTL_SECONDS = 3600.0
_DECIMAL = re.compile(
    r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", re.ASCII
)


@dataclass(frozen=True, slots=True)
class HistoryCacheKey:
    provider: str
    mapping_version: str
    symbol: str
    start: date
    end: date
    price_basis: str

    def __post_init__(self):
        if (
            self.provider != "fmp"
            or self.mapping_version != "raw-eod-v1"
            or self.price_basis != "raw"
            or type(self.start) is not date
            or type(self.end) is not date
            or self.start > self.end
            or (self.end - self.start).days >= MAX_BARS
        ):
            raise HistoryCacheError()
        try:
            _symbol(self.symbol)
        except ProviderResponseError:
            raise HistoryCacheError() from None


@dataclass(frozen=True, slots=True)
class HistoryCacheEntry:
    key: HistoryCacheKey
    retrieved_at: datetime
    bars: tuple[PriceBar, ...]

    def __post_init__(self):
        if not isinstance(self.key, HistoryCacheKey):
            raise HistoryCacheError()
        try:
            self.key.__post_init__()
            HistoryObservation(self.bars, self.retrieved_at)
            for bar in self.bars:
                bar.__post_init__()
        except ProviderResponseError:
            raise HistoryCacheError() from None
        if any(
            bar.symbol != self.key.symbol
            or not self.key.start <= bar.date <= self.key.end
            for bar in self.bars
        ):
            raise HistoryCacheError()


def _key_order(key):
    return (
        key.provider,
        key.mapping_version,
        key.symbol,
        key.start.isoformat(),
        key.end.isoformat(),
        key.price_basis,
    )


def _entry_object(entry):
    key = entry.key
    return {
        "key": dict(
            zip(
                (
                    "provider",
                    "mapping_version",
                    "symbol",
                    "start",
                    "end",
                    "price_basis",
                ),
                _key_order(key),
            )
        ),
        "retrieved_at": entry.retrieved_at.astimezone(timezone.utc).isoformat(
            timespec="microseconds"
        ),
        "bars": [
            {
                "symbol": bar.symbol,
                "date": bar.date.isoformat(),
                **{
                    field: str(getattr(bar, field))
                    for field in ("open", "high", "low", "close")
                },
                "adjusted_close": None,
                "volume": bar.volume,
            }
            for bar in entry.bars
        ],
    }


def _strings(value):
    if isinstance(value, str):
        if len(value) > MAX_STRING:
            raise HistoryCacheError()
    elif isinstance(value, dict):
        for key, item in value.items():
            _strings(key)
            _strings(item)
    elif isinstance(value, list):
        for item in value:
            _strings(item)


def _encode(entries):
    value = {
        "format": "stock-tracker-history-cache",
        "version": 1,
        "entries": [_entry_object(entry) for entry in entries],
    }
    _strings(value)
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


def cache_admissible(entry: HistoryCacheEntry) -> bool:
    """Check a complete single result before repository admission/eviction."""
    if len(entry.bars) > MAX_BARS:
        return False
    try:
        return len(_encode([entry])) <= MAX_BYTES
    except HistoryCacheError:
        return False


def _object(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise HistoryCacheError()
    return value


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise HistoryCacheError()
        value[key] = item
    return value


def _reject_constant(value):
    raise HistoryCacheError()


def _date(value):
    if not isinstance(value, str):
        raise HistoryCacheError()
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise HistoryCacheError()
    return parsed


def _decode(raw):
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
        _strings(value)
        _object(value, ("format", "version", "entries"))
        if (
            value["format"] != "stock-tracker-history-cache"
            or type(value["version"]) is not int
            or value["version"] != 1
            or type(value["entries"]) is not list
            or len(value["entries"]) > MAX_ENTRIES
        ):
            raise HistoryCacheError()
        entries = {}
        for item in value["entries"]:
            _object(item, ("key", "retrieved_at", "bars"))
            key = _object(
                item["key"],
                (
                    "provider",
                    "mapping_version",
                    "symbol",
                    "start",
                    "end",
                    "price_basis",
                ),
            )
            key = HistoryCacheKey(
                key["provider"],
                key["mapping_version"],
                key["symbol"],
                _date(key["start"]),
                _date(key["end"]),
                key["price_basis"],
            )
            stamp = item["retrieved_at"]
            if not isinstance(stamp, str):
                raise HistoryCacheError()
            received = datetime.fromisoformat(stamp)
            if (
                received.utcoffset() != timedelta(0)
                or received.isoformat(timespec="microseconds") != stamp
            ):
                raise HistoryCacheError()
            if type(item["bars"]) is not list or not 1 <= len(item["bars"]) <= MAX_BARS:
                raise HistoryCacheError()
            bars = []
            for bar in item["bars"]:
                _object(
                    bar,
                    (
                        "symbol",
                        "date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "adjusted_close",
                        "volume",
                    ),
                )
                numbers = []
                for field in ("open", "high", "low", "close"):
                    text = bar[field]
                    if not isinstance(text, str) or _DECIMAL.fullmatch(text) is None:
                        raise HistoryCacheError()
                    numbers.append(Decimal(text))
                if bar["adjusted_close"] is not None:
                    raise HistoryCacheError()
                bars.append(
                    PriceBar(
                        bar["symbol"], _date(bar["date"]), *numbers, None, bar["volume"]
                    )
                )
            entry = HistoryCacheEntry(key, received, tuple(bars))
            if key in entries:
                raise HistoryCacheError()
            entries[key] = entry
        return entries
    except (
        ValueError,
        TypeError,
        KeyError,
        UnicodeError,
        InvalidOperation,
        RecursionError,
        ProviderResponseError,
    ):
        raise HistoryCacheError() from None


class JsonHistoryCacheRepository:
    """Explicit path/clock; IO starts only at get or put."""

    def __init__(self, path: Path, clock: Callable[[], datetime]):
        if not isinstance(path, Path) or not callable(clock):
            raise ValueError("History cache requires a Path and clock.")
        self._path, self._clock = path, clock

    def _read(self):
        if not self._path.parent.is_dir():
            raise HistoryCacheError()
        try:
            mode = self._path.lstat().st_mode
        except FileNotFoundError:
            return {}
        if not stat.S_ISREG(mode):
            raise HistoryCacheError()
        with self._path.open("rb") as stream:
            if os.fstat(stream.fileno()).st_size > MAX_BYTES:
                raise HistoryCacheError()
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise HistoryCacheError()
        return _decode(raw)

    def get(self, key: HistoryCacheKey) -> HistoryCacheEntry | None:
        if not isinstance(key, HistoryCacheKey):
            raise HistoryCacheError()
        try:
            return self._read().get(key)
        except OSError:
            raise HistoryCacheError() from None

    def put(self, entry: HistoryCacheEntry) -> None:
        if not isinstance(entry, HistoryCacheEntry) or not cache_admissible(entry):
            raise HistoryCacheError()
        temporary = None
        try:
            entries = self._read()
            now = self._clock()
            if not isinstance(now, datetime) or now.utcoffset() != timedelta(0):
                raise ValueError("History cache clock must return aware UTC.")
            entries = {
                key: value
                for key, value in entries.items()
                if 0 <= (now - value.retrieved_at).total_seconds() < TTL_SECONDS
            }
            entries[entry.key] = entry
            while True:
                candidate = _encode(list(entries.values()))
                if len(entries) <= MAX_ENTRIES and len(candidate) <= MAX_BYTES:
                    break
                oldest = min(
                    entries,
                    key=lambda key: (entries[key].retrieved_at, _key_order(key)),
                )
                del entries[oldest]
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=self._path.parent, prefix=".history-cache-", delete=False
            ) as stream:
                temporary = Path(stream.name)
                stream.write(candidate)
                stream.flush()
            self._read()  # Refuse concurrent unknown/type-changed targets before publication.
            os.replace(temporary, self._path)
        except OSError:
            raise HistoryCacheError() from None
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    raise HistoryCacheError() from None
