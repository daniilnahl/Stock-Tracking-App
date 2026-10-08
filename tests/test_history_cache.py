"""Synthetic neutral history cache policy and failure-preservation evidence."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, localcontext
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from stock_tracker.exceptions import (
    HistoryCacheError,
    HistoryRangeError,
    ProviderResponseError,
    ProviderUnavailableError,
)
from stock_tracker.persistence import history_cache as storage
from stock_tracker.persistence.history_cache import (
    HistoryCacheEntry,
    HistoryCacheKey,
    JsonHistoryCacheRepository,
)
from stock_tracker.providers.history_cache import CachedHistoricalMarketDataProvider
from stock_tracker.providers.models import HistoryObservation, PriceBar
from stock_tracker.providers.transport import ProviderPolicy

START, END = date(2020, 1, 2), date(2020, 1, 6)
NOW = datetime(2020, 1, 7, 12, tzinfo=timezone.utc)


def bar(symbol="AAPL", session=START, price="100.123456789012345678901234567890"):
    return PriceBar(
        symbol,
        session,
        Decimal(price),
        Decimal("120"),
        Decimal("99"),
        Decimal("110.0000"),
        None,
        0,
    )


def entry(symbol="AAPL", received=NOW):
    return HistoryCacheEntry(
        HistoryCacheKey("fmp", "raw-eod-v1", symbol, START, END, "raw"),
        received,
        (bar(symbol),),
    )


def policy(ttl=3600.0):
    return ProviderPolicy(
        10.0,
        2,
        frozenset({408, 500, 502, 503, 504}),
        0.5,
        2.0,
        30.0,
        False,
        0.0,
        ttl,
        False,
    )


@pytest.fixture
def rig(tmp_path):
    state = SimpleNamespace(
        now=NOW, calls=[], path=tmp_path / "history.json", failure=None
    )

    def load(symbol, start, end):
        state.calls.append((symbol, start, end))
        if state.failure:
            raise state.failure
        return HistoryObservation((bar(symbol, start),), state.now)

    state.repo = JsonHistoryCacheRepository(state.path, lambda: state.now)
    state.adapter = lambda ttl=3600.0: CachedHistoricalMarketDataProvider(
        repository=state.repo, loader=load, clock=lambda: state.now, policy=policy(ttl)
    )
    return state


def test_receipt_precision_normalization_fresh_adapter_and_mutation(rig):
    with localcontext() as context:
        context.prec = 3
        first = rig.adapter().get_price_history(" aapl ", START, END)
        first.clear()
        second = rig.adapter().get_price_history("AAPL", START, END)
    assert len(rig.calls) == 1
    assert second == [bar()]
    assert second[0].open.as_tuple().exponent == -30
    assert str(second[0].close) == "110.0000"
    assert rig.repo.get(entry().key).retrieved_at == NOW
    assert (
        json.loads(rig.path.read_text())["entries"][0]["retrieved_at"]
        == "2020-01-07T12:00:00.000000+00:00"
    )
    with pytest.raises(FrozenInstanceError):
        second[0].close = Decimal(0)


def test_two_fresh_fmp_adapters_share_sidecar_and_suppress_http(rig):
    from stock_tracker.providers.fmp import FMPMarketDataProvider
    from stock_tracker.providers.transport import HttpResponse
    requests = []
    def get(url, *, headers, timeout_seconds):
        requests.append(url)
        return HttpResponse(200, {}, b'[{"symbol":"AAPL","date":"2020-01-02",'
            b'"adjOpen":100.12345678901234567890,"adjHigh":120,"adjLow":99,"adjClose":110,"volume":0}]')
    def adapter():
        synthetic_header = "synthetic-cache-fixture"
        upstream = FMPMarketDataProvider(api_key=synthetic_header,
            transport=SimpleNamespace(get=get), policy=policy(), clock=lambda: rig.now,
            monotonic=lambda: 0.0, sleep=lambda delay: None, jitter=lambda upper: 0.0)
        return CachedHistoricalMarketDataProvider(repository=JsonHistoryCacheRepository(rig.path, lambda: rig.now),
            loader=upstream._load_price_history, clock=lambda: rig.now, policy=policy())
    first = adapter().get_price_history(" aapl ", START, END)
    second = adapter().get_price_history("AAPL", START, END)
    assert len(requests) == 1 and first == second and first is not second
    assert "historical-price-eod/non-split-adjusted" in requests[0]
    assert str(second[0].open) == "100.12345678901234567890"


@pytest.mark.parametrize(
    "seconds,requests", [(0, 1), (3599.999999, 1), (3600, 2), (3601, 2), (-1, 2)]
)
def test_exact_freshness_boundaries(rig, seconds, requests):
    rig.adapter().get_price_history("AAPL", START, END)
    rig.now += timedelta(seconds=seconds)
    rig.adapter().get_price_history("AAPL", START, END)
    assert len(rig.calls) == requests


def test_exact_key_separation(rig):
    adapter = rig.adapter()
    for symbol, start, end in [
        ("AAPL", START, END),
        ("OTHER", START, END),
        ("AAPL", START, date(2020, 1, 5)),
        ("AAPL", date(2020, 1, 3), END),
    ]:
        adapter.get_price_history(symbol, start, end)
        adapter.get_price_history(symbol, start, end)
    assert len(rig.calls) == 4
    assert len(json.loads(rig.path.read_text())["entries"]) == 4


def test_zero_bypasses_all_cache_io(rig, monkeypatch):
    def denied(*args):
        pytest.fail("Cache IO with zero TTL")

    monkeypatch.setattr(rig.repo, "get", denied)
    monkeypatch.setattr(rig.repo, "put", denied)
    rig.adapter(0.0).get_price_history("AAPL", START, END)
    rig.adapter(0.0).get_price_history("AAPL", START, END)
    assert len(rig.calls) == 2 and not rig.path.exists()


@pytest.mark.parametrize(
    "start,end",
    [
        (None, END),
        (START, None),
        (NOW, END),
        (END, START),
        (START, NOW.date()),
        (date(2000, 1, 1), END),
    ],
)
def test_invalid_range_precedes_cache_and_loader(rig, start, end):
    rig.path.write_bytes(b"corrupt")
    with pytest.raises(HistoryRangeError):
        rig.adapter().get_price_history("AAPL", start, end)
    assert not rig.calls and rig.path.read_bytes() == b"corrupt"


def test_missing_read_and_constructor_are_io_free(tmp_path, monkeypatch):
    path = tmp_path / "absent-parent" / "history.json"
    def clock():
        pytest.fail("Constructor clock access")
    repository = JsonHistoryCacheRepository(path, clock)
    CachedHistoricalMarketDataProvider(
        repository=repository, loader=clock, clock=clock, policy=policy()
    )
    assert not path.parent.exists()
    with pytest.raises(HistoryCacheError):
        repository.get(entry().key)
    repo = JsonHistoryCacheRepository(tmp_path / "missing.json", lambda: NOW)
    assert repo.get(entry().key) is None and not (tmp_path / "missing.json").exists()


def test_source_subprocess_reuse(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for mode in ("write", "read"):
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                str(root / "tests" / "history_cache_probe.py"),
                str(root / "src"),
                str(tmp_path / "history.json"),
                mode,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == result.stderr == ""


@pytest.mark.parametrize("cached", [entry("OTHER"), "invalid"])
def test_hit_boundary_rejects_wrong_key_or_type(cached):
    adapter = CachedHistoricalMarketDataProvider(
        repository=SimpleNamespace(get=lambda key: cached),
        loader=lambda *args: pytest.fail("Loader after invalid hit"),
        clock=lambda: NOW,
        policy=policy(),
    )
    with pytest.raises(ProviderResponseError if isinstance(cached, HistoryCacheEntry) else HistoryCacheError):
        adapter.get_price_history("AAPL", START, END)


def test_invalid_typed_range_before_clock():
    adapter = CachedHistoricalMarketDataProvider(
        repository=None,
        loader=lambda *args: None,
        clock=lambda: pytest.fail("Clock before type validation"),
        policy=policy(),
    )
    with pytest.raises(HistoryRangeError):
        adapter.get_price_history("AAPL", None, END)


@pytest.mark.parametrize(
    "failure", [ProviderUnavailableError(), ProviderResponseError()]
)
def test_failure_never_returns_stale_or_changes_file(rig, failure):
    rig.adapter().get_price_history("AAPL", START, END)
    original = rig.path.read_bytes()
    rig.now += timedelta(hours=1)
    rig.failure = failure
    with pytest.raises(type(failure)):
        rig.adapter().get_price_history("AAPL", START, END)
    assert rig.path.read_bytes() == original
    assert len(rig.calls) == 2


@pytest.mark.parametrize(
    "observed",
    [
        HistoryObservation((bar("OTHER"),), NOW),
        HistoryObservation((bar(session=date(2020, 1, 1)),), NOW),
        None,
    ],
)
def test_loader_mismatch_not_published(rig, observed):
    adapter = CachedHistoricalMarketDataProvider(
        repository=rig.repo,
        loader=lambda *args: observed,
        clock=lambda: NOW,
        policy=policy(),
    )
    with pytest.raises(ProviderResponseError):
        adapter.get_price_history("AAPL", START, END)
    assert not rig.path.exists()


def envelope():
    return json.loads(storage._encode([entry()]))


def corrupt(value, case):
    item = value["entries"][0]
    if case == "format":
        value["format"] = "unknown"
    elif case == "future-version":
        value["version"] = 2
    elif case == "bool-version":
        value["version"] = True
    elif case == "unknown-envelope":
        value["extra"] = 1
    elif case == "unknown-entry":
        item["extra"] = 1
    elif case == "unknown-key":
        item["key"]["extra"] = 1
    elif case == "provider":
        item["key"]["provider"] = "other"
    elif case == "mapping":
        item["key"]["mapping_version"] = "other"
    elif case == "basis":
        item["key"]["price_basis"] = "adjusted"
    elif case == "lowercase":
        item["key"]["symbol"] = "aapl"
    elif case == "range":
        item["key"]["end"] = "2020-01-01"
    elif case == "compact-date":
        item["key"]["start"] = "20200102"
    elif case == "duplicate-entry":
        value["entries"].append(item)
    elif case == "empty":
        item["bars"] = []
    elif case == "duplicate-date":
        item["bars"].append(item["bars"][0])
    elif case == "descending":
        item["bars"] = [dict(item["bars"][0], date="2020-01-03"), item["bars"][0]]
    elif case == "bar-identity":
        item["bars"][0]["symbol"] = "OTHER"
    elif case == "bar-range":
        item["bars"][0]["date"] = "2020-01-01"
    elif case == "missing-field":
        del item["bars"][0]["open"]
    elif case == "unknown-bar":
        item["bars"][0]["extra"] = 1
    elif case == "adjusted":
        item["bars"][0]["adjusted_close"] = "100"
    elif case == "numeric":
        item["bars"][0]["open"] = 100
    elif case == "negative":
        item["bars"][0]["open"] = "-1"
    elif case == "ohlc":
        item["bars"][0]["open"] = "121"
    elif case == "whitespace":
        item["bars"][0]["open"] = " 100"
    elif case == "underscore":
        item["bars"][0]["open"] = "1_00"
    elif case == "nonfinite":
        item["bars"][0]["open"] = "NaN"
    elif case == "unicode-digit":
        item["bars"][0]["open"] = "١٠٠"
    elif case == "long-string":
        item["bars"][0]["open"] = "1" * 4097
    elif case == "bool-volume":
        item["bars"][0]["volume"] = True
    elif case == "negative-volume":
        item["bars"][0]["volume"] = -1
    elif case == "big-volume":
        item["bars"][0]["volume"] = 9223372036854775808
    elif case == "fraction-volume":
        item["bars"][0]["volume"] = 1.5
    elif case == "naive":
        item["retrieved_at"] = "2020-01-07T12:00:00.000000"
    elif case == "Z":
        item["retrieved_at"] = "2020-01-07T12:00:00.000000Z"
    elif case == "short-stamp":
        item["retrieved_at"] = "2020-01-07T12:00:00+00:00"
    elif case == "offset":
        item["retrieved_at"] = "2020-01-07T13:00:00.000000+01:00"
    return json.dumps(value).encode()


@pytest.mark.parametrize(
    "case",
    [
        "format",
        "future-version",
        "bool-version",
        "unknown-envelope",
        "unknown-entry",
        "unknown-key",
        "provider",
        "mapping",
        "basis",
        "lowercase",
        "range",
        "compact-date",
        "duplicate-entry",
        "empty",
        "duplicate-date",
        "descending",
        "bar-identity",
        "bar-range",
        "missing-field",
        "unknown-bar",
        "adjusted",
        "numeric",
        "negative",
        "ohlc",
        "whitespace",
        "underscore",
        "nonfinite",
        "unicode-digit",
        "long-string",
        "bool-volume",
        "negative-volume",
        "big-volume",
        "fraction-volume",
        "naive",
        "Z",
        "short-stamp",
        "offset",
    ],
)
def test_corrupt_cache_blocks_http_and_is_preserved(rig, case):
    original = corrupt(envelope(), case)
    rig.path.write_bytes(original)
    with pytest.raises(
        HistoryCacheError, match="^Historical cache operation failed\\.$"
    ):
        rig.adapter().get_price_history("AAPL", START, END)
    with pytest.raises(HistoryCacheError):
        rig.repo.put(entry())
    assert rig.path.read_bytes() == original and rig.calls == []


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"not JSON",
        b"\xff",
        b'{"format":1,"format":2}',
        b'{"format":NaN}',
        b"[" * 2000,
    ],
)
def test_malformed_json_preservation(rig, raw):
    rig.path.write_bytes(raw)
    with pytest.raises(HistoryCacheError):
        rig.repo.get(entry().key)
    assert rig.path.read_bytes() == raw


def test_directory_and_unreadable_refused(rig, monkeypatch):
    rig.path.mkdir()
    with pytest.raises(HistoryCacheError):
        rig.repo.get(entry().key)
    rig.path.rmdir()
    rig.repo.put(entry())
    original = rig.path.read_bytes()
    real = Path.open

    def denied(path, *args, **kwargs):
        if path == rig.path:
            raise PermissionError("sensitive path")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(HistoryCacheError):
        rig.repo.get(entry().key)
    monkeypatch.setattr(Path, "open", real)
    assert rig.path.read_bytes() == original


def test_symlink_refused(rig, tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.write_bytes(b"unrelated")
    try:
        rig.path.symlink_to(target)
    except OSError:
        # Windows without symlink privilege: exercise the same lstat boundary
        # with a synthetic symlink mode. POSIX runs the actual symlink path.
        import stat

        real = Path.lstat
        monkeypatch.setattr(
            Path,
            "lstat",
            lambda path: SimpleNamespace(st_mode=stat.S_IFLNK)
            if path == rig.path
            else real(path),
        )
    with pytest.raises(HistoryCacheError):
        rig.repo.get(entry().key)
    with pytest.raises(HistoryCacheError):
        rig.repo.put(entry())
    assert target.read_bytes() == b"unrelated" and rig.path.is_symlink()


def test_expired_then_lexical_oldest_eviction(rig):
    for number in range(32):
        rig.repo.put(entry(f"S{number:02}"))
    rig.repo.put(entry("ZZ"))
    assert rig.repo.get(entry("S00").key) is None
    assert rig.repo.get(entry("S01").key) is not None
    rig.now += timedelta(hours=1)
    rig.repo.put(entry("NEW", rig.now))
    assert len(json.loads(rig.path.read_text())["entries"]) == 1


def test_distinct_receipt_oldest_and_combined_byte_eviction(rig, monkeypatch):
    old = entry("Z", NOW - timedelta(seconds=2))
    recent = entry("A", NOW - timedelta(seconds=1))
    rig.repo.put(old)
    rig.repo.put(recent)
    new = entry("NEW")
    limit = len(storage._encode([recent, new]))
    assert len(storage._encode([old, recent])) <= limit
    monkeypatch.setattr(storage, "MAX_BYTES", limit)
    rig.repo.put(new)
    assert rig.repo.get(old.key) is None
    assert rig.repo.get(recent.key) == recent
    assert rig.repo.get(new.key) == new


def test_original_loader_receipt_is_not_insertion_time(rig):
    received = NOW - timedelta(seconds=300)
    adapter = CachedHistoricalMarketDataProvider(repository=rig.repo,
        loader=lambda *args: HistoryObservation((bar(),), received),
        clock=lambda: rig.now, policy=policy())
    adapter.get_price_history("AAPL", START, END)
    assert rig.repo.get(entry().key).retrieved_at == received
    rig.now = received + timedelta(seconds=3600)
    calls = []
    adapter = CachedHistoricalMarketDataProvider(repository=rig.repo,
        loader=lambda *args: (calls.append(args) or HistoryObservation((bar(),), rig.now)),
        clock=lambda: rig.now, policy=policy())
    adapter.get_price_history("AAPL", START, END)
    assert len(calls) == 1


def test_exact_count_and_string_bounds(rig):
    start = date(2000, 1, 1)
    end = start + timedelta(days=3659)
    text = "100." + "0" * 4092
    decimal = Decimal(text)
    bounded_bar = PriceBar("AAPL", start, decimal, decimal, decimal, decimal, None, 9223372036854775807)
    key = HistoryCacheKey("fmp", "raw-eod-v1", "AAPL", start, end, "raw")
    bars = tuple(replace(bounded_bar, date=start + timedelta(days=index)) for index in range(3660))
    bounded = HistoryCacheEntry(key, NOW, bars)
    # Individual 4096-character strings are permitted even though this entire
    # large result exceeds the separate byte bound.
    one = HistoryCacheEntry(key, NOW, (bounded_bar,))
    assert storage.cache_admissible(one)
    rig.repo.put(one)
    assert rig.repo.get(key) == one
    assert not storage.cache_admissible(bounded)
    normal = HistoryCacheEntry(key, NOW, tuple(replace(bar(), date=start + timedelta(days=index))
                                              for index in range(3660)))
    rig.repo.put(normal)
    assert len(rig.repo.get(key).bars) == 3660
    raw = json.loads(storage._encode([normal]))
    raw["entries"][0]["bars"].append(raw["entries"][0]["bars"][-1])
    rig.path.write_text(json.dumps(raw))
    with pytest.raises(HistoryCacheError):
        rig.repo.get(key)
    raw = envelope()
    raw["entries"] = [dict(raw["entries"][0], key=dict(raw["entries"][0]["key"], symbol=f"S{index}"),
        bars=[dict(raw["entries"][0]["bars"][0], symbol=f"S{index}")]) for index in range(33)]
    rig.path.write_text(json.dumps(raw))
    with pytest.raises(HistoryCacheError):
        rig.repo.get(entry().key)


def test_exact_byte_read_cap_and_oversized_individual_bypass(rig, monkeypatch):
    original = storage._encode([entry("OLD")])
    rig.path.write_bytes(original + b" " * (storage.MAX_BYTES - len(original)))
    assert rig.repo.get(entry("OLD").key) == entry("OLD")
    with rig.path.open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(HistoryCacheError):
        rig.repo.get(entry("OLD").key)
    rig.path.write_bytes(original)
    # A bounded-string individual result may exceed the complete byte budget.
    monkeypatch.setattr(storage, "MAX_BYTES", len(original))
    longer = replace(bar(), open=Decimal("100." + "0" * 1000))
    adapter = CachedHistoricalMarketDataProvider(repository=rig.repo,
        loader=lambda *args: HistoryObservation((longer,), NOW), clock=lambda: NOW, policy=policy())
    monkeypatch.setattr(rig.repo, "put", lambda *args: pytest.fail("Byte-oversized insertion"))
    assert adapter.get_price_history("AAPL", START, END) == [longer]
    assert rig.path.read_bytes() == original


def test_resource_limits_and_individual_bypass_before_put(rig, monkeypatch):
    rig.repo.put(entry("OLD"))
    original = rig.path.read_bytes()
    # Very long exact Decimal spelling is valid provider data, exceeds cache string cap.
    huge = replace(bar(), open=Decimal("100." + "0" * 4096))
    adapter = CachedHistoricalMarketDataProvider(
        repository=rig.repo,
        loader=lambda *args: HistoryObservation((huge,), NOW),
        clock=lambda: NOW,
        policy=policy(),
    )
    monkeypatch.setattr(
        rig.repo, "put", lambda *args: pytest.fail("Oversized insertion")
    )
    assert adapter.get_price_history("AAPL", START, END) == [huge]
    assert rig.path.read_bytes() == original
    monkeypatch.setattr(storage, "MAX_BYTES", len(original) - 1)
    with pytest.raises(HistoryCacheError):
        rig.repo.get(entry("OLD").key)
    assert rig.path.read_bytes() == original


@pytest.mark.parametrize("failure", ["temp", "write", "flush", "replace", "recheck"])
def test_atomic_failure_preserves_target_and_cleans_only_owned_temp(
    rig, monkeypatch, failure
):
    rig.repo.put(entry("OLD"))
    original = rig.path.read_bytes()
    unrelated = rig.path.parent / ".history-cache-unrelated"
    unrelated.write_bytes(b"unrelated")

    def denied(*args, **kwargs):
        raise OSError("sensitive detail")

    if failure == "temp":
        monkeypatch.setattr(storage.tempfile, "NamedTemporaryFile", denied)
    elif failure in ("write", "flush"):
        real = storage.tempfile.NamedTemporaryFile

        class Broken:
            def __init__(self, *args, **kwargs):
                self.file = real(*args, **kwargs)

            def __enter__(self):
                self.file.__enter__()
                return self

            @property
            def name(self):
                return self.file.name

            def write(self, value):
                if failure == "write":
                    denied()
                return self.file.write(value)

            def flush(self):
                denied()

            def __exit__(self, *args):
                return self.file.__exit__(*args)

        monkeypatch.setattr(storage.tempfile, "NamedTemporaryFile", Broken)
    elif failure == "replace":
        monkeypatch.setattr(storage.os, "replace", denied)
    else:
        real = rig.repo._read
        calls = []

        def changed():
            calls.append(1)
            if len(calls) == 2:
                rig.path.write_bytes(b"concurrent unknown target")
            return real()

        monkeypatch.setattr(rig.repo, "_read", changed)
    with pytest.raises(HistoryCacheError):
        rig.repo.put(entry("NEW"))
    assert rig.path.read_bytes() == (
        b"concurrent unknown target" if failure == "recheck" else original
    )
    assert unrelated.read_bytes() == b"unrelated"
    assert list(rig.path.parent.glob(".history-cache-*")) == [unrelated]
