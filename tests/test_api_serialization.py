"""Exact neutral wire projections, known values and forged-output refusal."""

from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
import json

import pytest

from stock_tracker.api import ApiServices
from stock_tracker.api.errors import ApiFailure
from stock_tracker.api.json_response import BoundedJSONResponse
from stock_tracker.api.schemas import HistoryResponse, WatchlistResponse
from stock_tracker.api.serialization import history_payload, watchlist_payload
from stock_tracker.domain import PositionSnapshot, Stock
from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord
from stock_tracker.providers.models import PriceBar
from stock_tracker.services.history import HistoryService
from stock_tracker.services.models import EntryView, HistoryView
from stock_tracker.services.watchlists import WatchlistService


def entry(*, quantity="10", cost="100", price="120.000", symbol="AAPL", exchange="NASDAQ"):
    return WatchlistEntry(Stock(symbol, "Fictional", exchange), Decimal(quantity),
                         None if cost is None else Decimal(cost), None if price is None else Decimal(price),
                         "saved sector", "N/A", "unknown label", "opaque $5B", *("saved 0.0%" for _ in range(8)))


def view(*entries):
    service = WatchlistService(None, namespace="menu_watchlist", legacy_present=lambda: False)
    return service.view(WatchlistRecord("menu_watchlist", "Synthetic", entries))


def test_exact_owned_missing_unowned_zero_and_duplicate_projection():
    rows = (entry(), entry(quantity="0", cost=None, price="0"),
            entry(quantity="0", cost="0", price=None), entry(quantity="0.000000000000000001", cost="1E-20", price="0"),
            entry(symbol="AAPL", exchange=None))
    neutral = view(*rows)
    payload = watchlist_payload(neutral)
    WatchlistResponse.model_validate(payload)
    assert [row["ordinal"] for row in payload["entries"]] == list(range(5))
    owned = payload["entries"][0]
    assert owned["snapshot"] == {"cost_basis": "1000", "market_value": "1200.000",
                                 "unrealized_pnl": "200.000", "unrealized_return": "0.200"}
    assert owned["current_price"] == "120.000"
    assert owned["metadata"]["market_cap"] == "opaque $5B"
    assert payload["provenance"] == {"source": None, "observed_at": None, "retrieved_at": None, "freshness": "unknown"}
    assert payload["entries"][1]["snapshot"] is None and payload["entries"][1]["current_price"] == "0"
    assert payload["entries"][2]["snapshot"] == {"cost_basis": "0", "market_value": None, "unrealized_pnl": None, "unrealized_return": None}
    assert payload["entries"][3]["quantity"] == "1E-18"
    assert payload["entries"][3]["snapshot"]["unrealized_return"] == "-1"
    assert neutral.record.entries == rows
    assert json.loads(BoundedJSONResponse(payload).body) == payload


@pytest.mark.parametrize("snapshot", [
    PositionSnapshot(None, Decimal("1200"), Decimal("200"), Decimal("0.2")),
    PositionSnapshot(Decimal("-1"), Decimal("1200"), Decimal("200"), Decimal("0.2")),
    PositionSnapshot(Decimal("1000"), None, Decimal("200"), None),
    PositionSnapshot(Decimal("1000"), Decimal("1200"), None, Decimal("0.2")),
    PositionSnapshot(Decimal("1000"), Decimal("1200"), Decimal("200"), None),
    PositionSnapshot(Decimal("0"), Decimal("1200"), Decimal("200"), Decimal("0.2")),
    PositionSnapshot(Decimal("1000"), Decimal("-1"), Decimal("200"), Decimal("0.2")),
    PositionSnapshot(Decimal("1000"), Decimal("NaN"), Decimal("200"), Decimal("0.2")),
    PositionSnapshot(Decimal("1000"), Decimal("1200"), Decimal("Infinity"), Decimal("0.2")),
    PositionSnapshot(Decimal("1000"), Decimal("1200"), Decimal("200"), 0.2),
    None,
])
def test_forged_snapshot_dependency_outputs_are_internal_errors(snapshot):
    original = view(entry())
    bad = replace(original, entries=(EntryView(original.record.entries[0], snapshot),))
    with pytest.raises(ApiFailure) as failure:
        watchlist_payload(bad)
    assert failure.value.code == "internal_error"


def test_row_association_and_mutated_stock_are_not_client_validation_errors():
    original = view(entry(), entry())
    bad = replace(original, entries=tuple(reversed(original.entries)))
    with pytest.raises(ApiFailure):
        watchlist_payload(bad)
    object.__setattr__(original.record.entries[0].stock, "symbol", " invalid ")
    # validated_record raises a safe PersistenceValidationError; HTTP mapping
    # classifies it as an internal dependency error, never invalid client input.
    from stock_tracker.api.errors import error_code
    try:
        watchlist_payload(original)
    except Exception as error:
        assert error_code(error) == "internal_error"
    else:
        pytest.fail("Malformed output must be refused")


def test_real_history_service_projection_sparse_raw_and_unknown_provenance():
    first, last = date(2024, 1, 2), date(2024, 1, 5)
    bars = [PriceBar("AAPL", day, Decimal("12.000"), Decimal("13.0"), Decimal("10.0"), Decimal("11.1234567890123456789"),
                     None, None if day == first else 0) for day in (first, last)]
    calls = []
    class Provider:
        def get_price_history(self, symbol, start, end):
            calls.append((symbol, start, end))
            return bars
    service = HistoryService(lambda ordinal: Provider(), clock=lambda: datetime(2024, 2, 1, tzinfo=timezone.utc))
    neutral = service.history(Stock("AAPL", exchange="NASDAQ"), ordinal=7, start=first, end=last)
    payload = history_payload(neutral, ordinal=7, services=ApiServices(history=service))
    HistoryResponse.model_validate(payload)
    assert calls == [("AAPL", first, last)]
    assert payload["provenance"] == {"source": None, "observed_at": None, "retrieved_at": None, "currency": None, "freshness": "unknown"}
    assert payload["bars"][0]["close"] == "11.1234567890123456789"
    assert payload["bars"][0]["adjusted_close"] is None and payload["bars"][0]["volume"] is None
    assert payload["bars"][1]["volume"] == 0
    assert payload["ordinal"] == 7 and payload["price_basis"] == "raw"
    production = history_payload(neutral, ordinal=7, services=ApiServices(history_source="fmp", history_cache_policy=True))
    assert production["provenance"]["freshness"] == "accepted_cache_policy"
    # A known provider name alone does not establish the cache policy.
    assert history_payload(neutral, ordinal=7, services=ApiServices(history_source="fmp"))["provenance"]["freshness"] == "unknown"


def test_history_non_raw_or_unordered_output_rejected_without_timestamp_fabrication():
    day = date(2024, 1, 2)
    bar = PriceBar("AAPL", day, Decimal(1), Decimal(1), Decimal(1), Decimal(1), None, 1)
    for bars in ((bar, bar), (), (replace(bar, adjusted_close=Decimal(1)),)):
        neutral = HistoryView(Stock("AAPL", exchange="NASDAQ"), day, day, bars)
        with pytest.raises(ApiFailure) as failure:
            history_payload(neutral, ordinal=0, services=ApiServices())
        assert failure.value.code == "internal_error"


def test_provenance_and_service_declarations_are_explicit_and_safe():
    for kwargs in ({"history_cache_policy": True}, {"history_source": "unapproved"}, {"history_enabled": 1}, {"watchlist": 1}):
        with pytest.raises(ValueError):
            ApiServices(**kwargs)
