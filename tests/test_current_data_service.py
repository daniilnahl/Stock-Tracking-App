"""Current service stages use real domain arithmetic and typed controlled providers."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from types import SimpleNamespace

import pytest


ERRORS = ("MarketDataUnavailableError", "InstrumentLookupInconclusiveError", "ProviderUnavailableError",
          "ProviderTimeoutError", "RateLimitError", "ProviderAuthenticationError", "ProviderAccessError",
          "ProviderRequestError", "ProviderResponseError", "InvalidTickerError")


@pytest.fixture
def rig():
    from stock_tracker.services.current_data import CurrentDataService
    from stock_tracker.providers.models import CompanyProfile, InstrumentIdentity, PeriodChanges
    stamp = datetime(2020, 1, 1, tzinfo=timezone.utc)
    state = SimpleNamespace(calls=[], acquisitions=[], failing=None, failure=None, fail_ordinal=None, raw={})
    state.profile = CompanyProfile("AAPL", "New company", "NASDAQ", "USD", "Tech", "US",
                                   Decimal("130"), Decimal("1000000000.123"), None, stamp)
    state.periods = PeriodChanges("AAPL", Decimal("12.345"), Decimal("-1.235"), Decimal(0), None,
                                  Decimal(6), Decimal(7), Decimal(8), Decimal(9), None, stamp)
    def acquire(operation, ordinal, *, on_configuration_failure=None):
        state.acquisitions.append((operation, ordinal, on_configuration_failure))
        def request(symbol):
            state.calls.append((operation, ordinal, symbol))
            if state.failing == operation and (state.fail_ordinal is None or ordinal == state.fail_ordinal):
                raise state.failure
            if operation in state.raw:
                return state.raw[operation]
            if operation == "resolve":
                return state.identity if hasattr(state, "identity") else InstrumentIdentity(symbol.strip().upper(), "NASDAQ", None, None)
            return replace(getattr(state, operation), symbol=symbol.strip().upper())
        return SimpleNamespace(resolve_symbol=request, get_company_profile=request, get_period_changes=request)
    state.source = acquire
    state.service = CurrentDataService(acquire)
    return state


def row(symbol="AAPL", *, exchange="NASDAQ", quantity="10", cost="100", price="120", currency="USD"):
    from stock_tracker.domain import Stock
    from stock_tracker.persistence.models import WatchlistEntry
    return WatchlistEntry(Stock(symbol, "Old company", exchange), Decimal(quantity),
                          None if cost is None else Decimal(cost), None if price is None else Decimal(price),
                          "Old sector", "Old country", currency, "old cap", "", "literal [x]", "0", "-", "N/A", None, "3", "4")


def record(*rows):
    from stock_tracker.persistence.models import WatchlistRecord
    return WatchlistRecord("menu_watchlist", "Saved", tuple(rows))


def test_constructor_and_successful_add_are_lazy_numeric_and_never_mutate_or_save(rig):
    original = record(row("EXISTING"))
    assert rig.calls == rig.acquisitions == []
    prepared = rig.service.prepare_add(original, "AAPL")
    assert prepared.status == "ready"
    assert rig.calls == [("resolve", None, "AAPL"), ("profile", None, "AAPL"), ("periods", None, "AAPL")]
    assert all(callback is None for _, _, callback in rig.acquisitions)
    ownership = rig.service.validate_ownership("0.2500", "100.0000")
    result = rig.service.finish_add(original, prepared, ownership)
    assert len(original.entries) == 1 and len(result.record.entries) == 2
    new = result.record.entries[1]
    assert (str(new.quantity), str(new.average_cost), new.current_price) == ("0.2500", "100.0000", Decimal(130))
    assert new.market_cap == new.price_1d == "N/A"  # Formatting belongs to #117.
    assert result.updates[0].profile.market_cap == Decimal("1000000000.123")
    assert result.updates[0].periods.day_1 == Decimal("12.345")
    assert len(rig.calls) == 3


def test_duplicate_lookup_occurs_before_duplicate_result_and_no_profile(rig):
    prepared = rig.service.prepare_add(record(row()), "AAPL")
    assert prepared.status == "duplicate" and prepared.profile is prepared.periods is None
    assert rig.calls == [("resolve", None, "AAPL")]


@pytest.mark.parametrize("stage", ["resolve", "profile", "periods"])
@pytest.mark.parametrize("name", ERRORS)
def test_add_error_categories_stop_at_stage_and_preserve_existing_state(rig, stage, name):
    import stock_tracker.exceptions as errors
    original = record(row("EXISTING"))
    rig.failing, rig.failure = stage, getattr(errors, name)()
    if stage == "resolve" and name == "InvalidTickerError":
        assert rig.service.prepare_add(original, "AAPL").status == "invalid"
    else:
        with pytest.raises(type(rig.failure)) as caught:
            rig.service.prepare_add(original, "AAPL")
        assert caught.value is rig.failure
    assert [operation for operation, _, _ in rig.calls] == ["resolve", "profile", "periods"][:["resolve", "profile", "periods"].index(stage) + 1]
    assert original.entries[0].stock.symbol == "EXISTING" and original.entries[0].current_price == 120


@pytest.mark.parametrize("identity", ["wrong_symbol", "wrong_exchange", "malformed"])
def test_malformed_lookup_fake_is_not_valid_or_invalid_candidate(rig, identity):
    from stock_tracker.exceptions import ProviderResponseError
    from stock_tracker.providers.models import InstrumentIdentity
    rig.identity = InstrumentIdentity("OTHER", "NASDAQ", None, None) if identity == "wrong_symbol" else (
        InstrumentIdentity("AAPL", "NYSE", None, None) if identity == "wrong_exchange" else object())
    with pytest.raises(ProviderResponseError):
        rig.service.prepare_add(record(), "AAPL")
    assert len(rig.calls) == 1


def test_invalid_local_domain_identity_fails_after_lookup_before_profile(rig):
    from stock_tracker.domain import DomainValidationError
    with pytest.raises(DomainValidationError):
        rig.service.prepare_add(record(), " AAPL ")
    assert rig.calls == [("resolve", None, " AAPL ")]


@pytest.mark.parametrize("field", ["quantity", "cost"])
@pytest.mark.parametrize("invalid", ["-1", "malformed-private-input", "1_0", "NaN", "Infinity", "", True, Decimal(1)])
def test_ownership_rejections_are_safe_and_no_repeated_provider_calls(rig, field, invalid):
    from stock_tracker.domain import DomainValidationError
    prepared = rig.service.prepare_add(record(), "AAPL")
    quantity, cost = (invalid, "100") if field == "quantity" else ("10", invalid)
    with pytest.raises(DomainValidationError) as caught:
        rig.service.validate_ownership(quantity, cost)
    assert "malformed-private-input" not in str(caught.value)
    valid = rig.service.validate_ownership(".25", "1e2")
    result = rig.service.finish_add(record(), prepared, valid)
    assert result.record.entries[0].quantity == Decimal(".25")
    assert len(rig.calls) == 3


@pytest.mark.parametrize("quantity,cost,price,expected_ratio", [
    ("10", "100", "120", "0.2"), ("0", "100", "120", None),
    ("10", "0", "120", None), (".25", "100", "80", "-.2"), ("0", "0", None, None),
])
def test_finish_add_reuses_known_value_domain_snapshots(rig, quantity, cost, price, expected_ratio):
    from stock_tracker.services import WatchlistService
    rig.profile = replace(rig.profile, price=None if price is None else Decimal(price))
    prepared = rig.service.prepare_add(record(), "AAPL")
    result = rig.service.finish_add(record(), prepared, rig.service.validate_ownership(quantity, cost))
    local = WatchlistService(object(), namespace="menu_watchlist", legacy_present=lambda: False)
    snapshot = local.view(result.record).entries[0].snapshot
    assert snapshot.unrealized_return == (None if expected_ratio is None else Decimal(expected_ratio))
    if price is None:
        assert snapshot.market_value is snapshot.unrealized_pnl is None


def test_finish_add_revalidates_mutated_inputs_before_publication(rig):
    from stock_tracker.domain import DomainValidationError
    prepared = rig.service.prepare_add(record(), "AAPL")
    ownership = rig.service.validate_ownership("10", "100")
    object.__setattr__(ownership, "quantity", Decimal("NaN"))
    with pytest.raises(DomainValidationError):
        rig.service.finish_add(record(), prepared, ownership)
    assert len(rig.calls) == 3


def test_precision_and_plain_decimal_grammar_reuse_legacy_parser(rig):
    from stock_tracker.compatibility.numeric import to_decimal as legacy
    from stock_tracker.services.numeric import to_decimal
    assert legacy is to_decimal
    text = "0.12345678901234567890123456789"
    with localcontext() as context:
        context.prec = 50
        result = rig.service.validate_ownership(text, " 1.25e2 ")
        assert str(result.quantity) == text and result.average_cost == Decimal(125)
        assert context.prec == 50


def test_refresh_success_emits_ordered_raw_stage_updates_without_mutating_rows(rig):
    original = record(row(), row("MSFT", quantity="3"))
    events = []
    result = rig.service.refresh(original, on_update=events.append)
    assert [(update.ordinal, update.profile is not None, update.periods is not None) for update in events] == [
        (0, True, False), (0, False, True), (1, True, False), (1, False, True),
    ]
    assert result.updates == tuple(events)
    assert [entry.current_price for entry in result.record.entries] == [Decimal(130), Decimal(130)]
    assert [entry.current_price for entry in original.entries] == [Decimal(120), Decimal(120)]
    assert all(entry.market_cap == "old cap" and entry.price_1d == "" for entry in result.record.entries)
    assert [operation for operation, _, _ in rig.calls] == ["profile", "periods", "profile", "periods"]


@pytest.mark.parametrize("stage", ["profile", "periods"])
@pytest.mark.parametrize("name", ERRORS)
def test_refresh_typed_failures_publish_only_accepted_stage_invalidation(rig, stage, name):
    import stock_tracker.exceptions as errors
    original = record(row())
    rig.failing, rig.failure = stage, getattr(errors, name)()
    events = []
    with pytest.raises(type(rig.failure)) as caught:
        rig.service.refresh(original, on_update=events.append)
    assert caught.value is rig.failure
    failure = events[-1]
    assert failure.profile is failure.periods is None
    assert failure.invalidate_periods is (stage == "periods")
    assert failure.entry.current_price == (None if stage == "profile" else Decimal(130))
    assert failure.entry.quantity == 10 and failure.entry.average_cost == 100
    assert len(events) == (1 if stage == "profile" else 2)
    assert original.entries[0].current_price == 120


def test_partial_second_row_refresh_retains_earlier_events_and_stops(rig):
    from stock_tracker.exceptions import ProviderUnavailableError
    rig.failing, rig.failure, rig.fail_ordinal = "profile", ProviderUnavailableError(), 1
    events = []
    original = record(row(), row("MSFT"), row("NEXT"))
    with pytest.raises(ProviderUnavailableError):
        rig.service.refresh(original, on_update=events.append)
    assert [event.ordinal for event in events] == [0, 0, 1]
    assert events[0].entry.current_price == 130 and events[-1].entry.current_price is None
    assert rig.calls == [("profile", 0, "AAPL"), ("periods", 0, "AAPL"), ("profile", 1, "MSFT")]
    assert all(entry.current_price == 120 for entry in original.entries)


@pytest.mark.parametrize("field,returned", [("exchange", "NYSE"), ("currency", "EUR")])
def test_known_identity_currency_conflict_invalidates_quote_not_holdings(rig, field, returned):
    from stock_tracker.exceptions import ProviderResponseError
    rig.profile = replace(rig.profile, **{field: returned})
    events = []
    with pytest.raises(ProviderResponseError):
        rig.service.refresh(record(row()), on_update=events.append)
    assert len(events) == 1 and events[0].entry.current_price is None
    assert events[0].entry.stock.exchange == "NASDAQ" and events[0].entry.currency == "USD"
    assert len(rig.calls) == 1


def test_absent_incoming_identity_keeps_known_fields_and_missing_differs_from_zero(rig):
    rig.profile = replace(rig.profile, exchange=None, currency=None, price=None, sector=None, country=None)
    result = rig.service.refresh(record(row()), on_update=lambda update: None)
    row_result = result.record.entries[0]
    assert row_result.stock.exchange == "NASDAQ" and row_result.currency == "USD"
    assert row_result.current_price is None and row_result.sector == row_result.country == "N/A"
    rig.profile = replace(rig.profile, price=Decimal(0))
    zero = rig.service.refresh(record(row()), on_update=lambda update: None)
    assert zero.record.entries[0].current_price == 0


def test_add_does_not_infer_missing_profile_identity_from_lookup(rig):
    rig.profile = replace(rig.profile, exchange=None, currency=None)
    prepared = rig.service.prepare_add(record(), "AAPL")
    result = rig.service.finish_add(record(), prepared, rig.service.validate_ownership("1", "100"))
    assert result.record.entries[0].stock.exchange is None
    assert result.record.entries[0].currency == "N/A"


@pytest.mark.parametrize("stage", ["profile", "periods"])
def test_programming_failures_propagate_without_synthetic_invalidation(rig, stage):
    rig.failing, rig.failure = stage, RuntimeError("programming")
    events = []
    with pytest.raises(RuntimeError) as caught:
        rig.service.refresh(record(row()), on_update=events.append)
    assert caught.value is rig.failure
    assert len(events) == (0 if stage == "profile" else 1)


@pytest.mark.parametrize("stage", ["profile", "periods"])
def test_configuration_acquisition_uses_exactly_one_service_owned_invalidation(rig, stage):
    from config import ConfigurationError
    from stock_tracker.cli.current_data import CurrentProviderSourceAdapter
    from stock_tracker.services.current_data import CurrentDataService
    failure = ConfigurationError("Safe synthetic configuration failure")
    def acquire(operation, ordinal):
        if operation == stage:
            raise failure
        return rig.source(operation, ordinal)
    service = CurrentDataService(CurrentProviderSourceAdapter(acquire))
    events = []
    with pytest.raises(ConfigurationError) as caught:
        service.refresh(record(row()), on_update=events.append)
    assert caught.value is failure
    assert len(events) == (1 if stage == "profile" else 2)
    assert events[-1].invalidate_periods is (stage == "periods")
    assert events[-1].entry.current_price == (None if stage == "profile" else Decimal(130))


@pytest.mark.parametrize("stage", ["resolve", "profile", "periods"])
def test_add_configuration_failure_has_no_progress_or_candidate(rig, stage):
    from config import ConfigurationError
    from stock_tracker.cli.current_data import CurrentProviderSourceAdapter
    from stock_tracker.services.current_data import CurrentDataService
    def acquire(operation, ordinal):
        if operation == stage:
            raise ConfigurationError("Safe synthetic configuration failure")
        return rig.source(operation, ordinal)
    original = record(row("EXISTING"))
    with pytest.raises(ConfigurationError):
        CurrentDataService(CurrentProviderSourceAdapter(acquire)).prepare_add(original, "AAPL")
    assert len(original.entries) == 1 and original.entries[0].current_price == 120


def test_config_adapter_is_lazy_and_only_catches_configuration_errors():
    from stock_tracker.cli.current_data import CurrentProviderSourceAdapter
    from stock_tracker.exceptions import ProviderUnavailableError
    calls = []
    failure = ProviderUnavailableError()
    def acquire(operation, ordinal):
        calls.append(operation)
        raise failure
    adapter = CurrentProviderSourceAdapter(acquire)
    assert calls == []
    with pytest.raises(ProviderUnavailableError):
        adapter("profile", 0, on_configuration_failure=lambda: pytest.fail("Wrong invalidation"))
    assert calls == ["profile"]


@pytest.mark.parametrize("stage", ["profile", "periods"])
@pytest.mark.parametrize("safe_error", [True, False])
def test_configuration_callback_errors_propagate_once_without_duplicate_invalidation(rig, stage, safe_error):
    from config import ConfigurationError
    from stock_tracker.cli.current_data import CurrentProviderSourceAdapter
    from stock_tracker.exceptions import PersistenceError
    from stock_tracker.services.current_data import CurrentDataService
    callback_error = PersistenceError() if safe_error else RuntimeError("callback programming failure")
    def acquire(operation, ordinal):
        if operation == stage:
            raise ConfigurationError("Safe synthetic configuration failure")
        return rig.source(operation, ordinal)
    events = []
    def publish(update):
        events.append(update)
        if update.profile is None:
            raise callback_error
    with pytest.raises(type(callback_error)) as caught:
        CurrentDataService(CurrentProviderSourceAdapter(acquire)).refresh(record(row()), on_update=publish)
    assert caught.value is callback_error
    assert len(events) == (1 if stage == "profile" else 2)
    assert events[-1].invalidate_periods is (stage == "periods")


@pytest.mark.parametrize("stage", ["profile", "periods"])
@pytest.mark.parametrize("safe_error", [True, False])
def test_success_progress_callback_errors_are_not_reclassified_as_provider_failures(rig, stage, safe_error):
    from stock_tracker.exceptions import PersistenceError
    callback_error = PersistenceError() if safe_error else RuntimeError("callback programming failure")
    events = []
    def publish(update):
        events.append(update)
        if (stage == "profile" and update.profile is not None) or (stage == "periods" and update.periods is not None):
            raise callback_error
    with pytest.raises(type(callback_error)) as caught:
        rig.service.refresh(record(row(), row("MSFT")), on_update=publish)
    assert caught.value is callback_error
    assert len(events) == (1 if stage == "profile" else 2)
    assert all(not update.invalidate_periods for update in events)
    assert [operation for operation, _, _ in rig.calls] == (["profile"] if stage == "profile" else ["profile", "periods"])


def test_malformed_frozen_input_is_rejected_before_provider_work(rig):
    from stock_tracker.exceptions import PersistenceValidationError
    original = record(row())
    object.__setattr__(original.entries[0], "quantity", Decimal("NaN"))
    with pytest.raises(PersistenceValidationError):
        rig.service.prepare_add(original, "AAPL")
    with pytest.raises(PersistenceValidationError):
        rig.service.refresh(original, on_update=lambda update: None)
    assert rig.calls == rig.acquisitions == []


@pytest.mark.parametrize("stage", ["profile", "periods"])
@pytest.mark.parametrize("kind", ["object", "wrong_symbol", "deleted_slot"])
def test_malformed_provider_fakes_are_safe_stage_failures(rig, stage, kind):
    from stock_tracker.exceptions import ProviderResponseError
    payload = replace(getattr(rig, stage))
    if kind == "object":
        payload = object()
    elif kind == "wrong_symbol":
        payload = replace(payload, symbol="OTHER")
    else:
        object.__delattr__(payload, "retrieved_at")
    rig.raw[stage] = payload
    events = []
    with pytest.raises(ProviderResponseError):
        rig.service.refresh(record(row()), on_update=events.append)
    assert len(events) == (1 if stage == "profile" else 2)
    assert events[-1].invalidate_periods is (stage == "periods")


def test_profile_candidate_storage_validation_is_inside_stage_invalidation(rig):
    from stock_tracker.exceptions import PersistenceValidationError
    rig.profile = replace(rig.profile, name="private\ud800")
    events = []
    with pytest.raises(PersistenceValidationError):
        rig.service.refresh(record(row()), on_update=events.append)
    assert len(events) == 1 and events[0].entry.current_price is None
    assert events[0].entry.stock.name == "Old company"
    assert len(rig.calls) == 1
