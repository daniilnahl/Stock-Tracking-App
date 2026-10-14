"""Real CLI adapters delegate to services and preserve facade compatibility."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import importlib
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner


@pytest.fixture(params=["menu_watchlist", "daniils_stock_method"])
def rig(request, monkeypatch):
    from stock import Stock
    from stock_tracker.providers import factory
    from stock_tracker.providers.models import CompanyProfile, InstrumentIdentity, PeriodChanges
    monkeypatch.setenv("FMP_API_KEY", "synthetic-adapter-runtime")
    module = importlib.reload(importlib.import_module(request.param))
    stamp = datetime(2020, 1, 1, tzinfo=timezone.utc)
    state = SimpleNamespace(module=module, calls=[], failure=None, profiles=0)
    state.profile = CompanyProfile("AAPL", "New name", "NASDAQ", "USD", "Tech", "US",
                                   Decimal(120), Decimal(10**9), None, stamp)
    state.periods = PeriodChanges("AAPL", *(Decimal("12.345") for _ in range(8)), None, stamp)
    def profile(symbol):
        state.calls.append(("profile", symbol))
        state.profiles += 1
        if state.failure is not None and state.profiles == 2:
            raise state.failure
        return replace(state.profile, symbol=symbol)
    provider = SimpleNamespace(
        resolve_symbol=lambda symbol: (state.calls.append(("resolve", symbol)) or
                                       InstrumentIdentity(symbol, "NASDAQ", None, None)),
        get_company_profile=profile,
        get_period_changes=lambda symbol: (state.calls.append(("periods", symbol)) or
                                           replace(state.periods, symbol=symbol)),
    )
    monkeypatch.setattr(factory, "create_market_data_provider", lambda key: provider)
    def denied(*a, **kw):
        pytest.fail("CLI reached legacy market-data orchestration")
    for name in ("get_stock_info", "get_price_over_time", "get_price_history", "graph_performance"):
        monkeypatch.setattr(Stock, name, denied)
    return state


def test_both_command_surfaces_execute_services_and_keep_existing_references(rig, monkeypatch):
    from stock_tracker.services.current_data import CurrentDataService
    from stock_tracker.services.watchlists import WatchlistService
    calls = []
    for cls, names in ((CurrentDataService, ("prepare_add", "validate_ownership", "finish_add", "refresh")),
                       (WatchlistService, ("load", "save", "view", "remove"))):
        for name in names:
            original = getattr(cls, name)
            def spy(self, *a, _name=name, _original=original, **kw):
                calls.append(_name)
                return _original(self, *a, **kw)
            monkeypatch.setattr(cls, name, spy)
    module, runner = rig.module, CliRunner()
    facade_list = module.current_watchlist.stocks
    assert runner.invoke(module.app, ["add-stock"], input="aapl\n.25\n100\n").exit_code == 0
    facade = facade_list[0]
    assert facade.market_cap == "1.000B" and facade.price_1d == "12.34"
    assert runner.invoke(module.app, ["show-stocks"]).exit_code == 0
    assert runner.invoke(module.app, ["refresh"]).exit_code == 0
    assert module.current_watchlist.stocks is facade_list and facade_list[0] is facade
    assert facade.market_cap == "1.000B" and facade._position.quantity == Decimal(".25")
    assert runner.invoke(module.app, ["remove-stock"], input="aapl\n").exit_code == 0
    assert facade_list == []
    assert {"prepare_add", "validate_ownership", "finish_add", "refresh", "load", "save", "view", "remove"} <= set(calls)


@pytest.mark.parametrize("aliased", [False, True])
def test_removal_distinguishes_aliases_from_equal_security_rows(rig, aliased):
    from stock import Stock
    module = rig.module
    first = Stock("AAPL", None, exchange="NASDAQ")
    other = Stock("MSFT", None)
    second = first if aliased else Stock("AAPL", None, exchange="NASDAQ")
    final = first if aliased else Stock("AAPL", None, exchange="NASDAQ")
    original = module.current_watchlist.stocks
    original[:] = [first, second, other, final]
    result = CliRunner().invoke(module.app, ["remove-stock"], input="aapl\n")
    assert result.exit_code == 0, result.output
    assert module.current_watchlist.stocks is original
    expected = [other, first] if aliased else [second, other]
    assert len(original) == 2 and all(a is b for a, b in zip(original, expected))
    assert [item.ticker_symbol for item in module.load_watchlist().stocks] == [item.ticker_symbol for item in expected]


def test_aliased_refresh_observes_earlier_publication_and_failure_never_saves(rig):
    from stock import Stock
    from stock_tracker.exceptions import ProviderUnavailableError
    module = rig.module
    runtime_key = "synthetic-adapter-runtime"
    facade = Stock("AAPL", runtime_key, name="Old", exchange="NASDAQ", currency="USD",
                   market_cap="old", current_price="100", amount_owned=".25", cost_basis="100")
    module.current_watchlist.stocks[:] = [facade, facade]
    module.save_watchlist(module.current_watchlist)
    before = module.WATCHLIST_FILE.read_bytes()
    rig.failure = ProviderUnavailableError()
    result = CliRunner().invoke(module.app, ["refresh"])
    assert result.exit_code == 1 and str(rig.failure) in result.output
    assert all(item is facade for item in module.current_watchlist.stocks)
    assert facade.name == "New name" and facade.market_cap == "1.000B"
    assert facade.price_1d == "12.34" and facade.current_price is None
    assert facade._position.quantity == Decimal(".25")
    assert module.WATCHLIST_FILE.read_bytes() == before
    assert rig.calls == [("profile", "AAPL"), ("periods", "AAPL"), ("profile", "AAPL")]


def test_projection_replay_keeps_profile_formatting_and_numeric_inputs(rig):
    from stock import Stock
    from stock_tracker.cli.presentation import apply_entry_update, project_prepared
    from stock_tracker.compatibility.watchlist_persistence import watchlist_to_record
    from stock_tracker.services.current_data import CurrentDataService
    from stock_tracker.providers import factory
    module = rig.module
    module.current_watchlist.stocks[:] = [Stock("AAPL", None, market_cap="old", price_1d="[literal]",
        amount_owned="0.2500", cost_basis="100.0000", current_price="100", exchange="NASDAQ")]
    record = watchlist_to_record(module.current_watchlist, module.WATCHLIST_NAMESPACE)
    service = CurrentDataService(lambda *a, **kw: factory.create_market_data_provider(None))
    published = [record.entries[0]]
    prepared = service.refresh(record, on_update=lambda update: published.append(apply_entry_update(published[-1], update)))
    replay = project_prepared(prepared).entries[0]
    assert replay == published[-1]
    assert replay.market_cap == "1.000B" and replay.price_1d == "12.34"
    assert str(replay.quantity) == "0.2500" and str(replay.average_cost) == "100.0000"
    assert record.entries[0].market_cap == "old" and record.entries[0].price_1d == "[literal]"


@pytest.mark.parametrize("invalid", ["ordinal", "symbol"])
def test_projection_rejects_unassociated_rows_before_rendering(rig, invalid):
    from stock import Stock
    from stock_tracker.cli.presentation import project_prepared
    from stock_tracker.compatibility.watchlist_persistence import watchlist_to_record
    from stock_tracker.exceptions import PersistenceValidationError
    from stock_tracker.services.models import EntryUpdate, PreparedWatchlist
    module = rig.module
    module.current_watchlist.stocks[:] = [Stock("AAPL", None)]
    record = watchlist_to_record(module.current_watchlist, module.WATCHLIST_NAMESPACE)
    update = EntryUpdate(0, record.entries[0], None, None, False)
    prepared = PreparedWatchlist(record, (update,))
    if invalid == "ordinal":
        object.__setattr__(update, "ordinal", 1)
    else:
        from stock_tracker.domain import Stock as Security
        object.__setattr__(update, "entry", replace(update.entry, stock=Security("OTHER")))
    with pytest.raises(PersistenceValidationError):
        project_prepared(prepared)
