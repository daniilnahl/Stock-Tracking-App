"""Real facade/domain/CLI state boundaries under typed fake providers."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import pickle
from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('price_1d', 'price_5d', 'price_30d', 'price_3m', 'price_6m', 'price_1y', 'price_3y', 'price_5y')
ERRORS = ('MarketDataUnavailableError', 'InstrumentLookupInconclusiveError', 'ProviderUnavailableError',
          'ProviderTimeoutError', 'RateLimitError', 'ProviderAuthenticationError', 'ProviderAccessError',
          'ProviderRequestError', 'ProviderResponseError')


@pytest.fixture
def rig(monkeypatch):
    from stock import Stock
    from stock_tracker.providers import factory
    from stock_tracker.providers.models import CompanyProfile, InstrumentIdentity, PeriodChanges, Quote
    stamp = datetime(2020, 1, 1, tzinfo=timezone.utc)
    state = SimpleNamespace(calls=[], keys=[], failing=None, failure=None, fail_symbol=None)
    state.profile = CompanyProfile('AAPL', 'New company', 'NASDAQ', 'USD', 'Tech', 'US', Decimal(130), Decimal(10**9), None, stamp)
    state.quote = Quote('AAPL', Decimal(80), None, None, None, stamp)
    state.periods = PeriodChanges('AAPL', Decimal('12.345'), Decimal('-1.235'), Decimal(0), None,
                                  Decimal(6), Decimal(7), Decimal(8), Decimal(9), None, stamp)
    def call(name, symbol):
        state.calls.append((name, symbol))
        if state.failing == name and (state.fail_symbol is None or state.fail_symbol == symbol):
            raise state.failure
        return InstrumentIdentity(symbol, 'NASDAQ', None, None) if name == 'resolve' else getattr(state, name)
    provider = SimpleNamespace(resolve_symbol=lambda symbol: call('resolve', symbol),
        get_company_profile=lambda symbol: call('profile', symbol), get_quote=lambda symbol: call('quote', symbol),
        get_period_changes=lambda symbol: call('periods', symbol))
    def create(key):
        state.keys.append(key)
        if state.failing == 'factory':
            raise state.failure
        return provider
    state.real_factory = factory.create_market_data_provider
    monkeypatch.setattr(factory, 'create_market_data_provider', create)
    dummy = 'synthetic-integration-runtime'
    state.stock = Stock('AAPL', dummy, name='Old company', exchange='NASDAQ', currency='USD',
                        sector='Old sector', country='Old country', market_cap='Old cap', current_price='120',
                        amount_owned='10', cost_basis='100')
    for field in FIELDS:
        setattr(state.stock, field, 'old')
    return state


def test_profile_candidate_publication_preserves_numeric_holdings_and_keys(rig):
    stock = rig.stock
    stock.get_stock_info()
    assert stock.name == stock._position.stock.name == 'New company'
    assert stock.exchange == stock._position.stock.exchange == 'NASDAQ'
    assert stock.current_price == '130' and stock.total_return == '30.0' and stock.market_cap == '1.000B'
    assert stock._position.quantity == Decimal(10) and stock._position.average_cost == Decimal(100)
    assert rig.calls == [('profile', 'AAPL')] and rig.keys == ['synthetic-integration-runtime']
    assert b'synthetic-integration-runtime' not in pickle.dumps(stock)


def test_absent_profile_metadata_keeps_known_identity_and_price_null_zero(rig):
    rig.profile = replace(rig.profile, exchange=None, currency=None, sector=None, country=None,
                          price=None, market_cap=None)
    rig.stock.get_stock_info()
    assert rig.stock.exchange == 'NASDAQ' and rig.stock.currency == 'USD'
    assert rig.stock.sector == rig.stock.country == rig.stock.market_cap == 'N/A'
    assert rig.stock.current_price is None and rig.stock.total_return == '-'
    rig.profile = replace(rig.profile, price=Decimal(0))
    rig.stock.get_stock_info()
    assert rig.stock.current_price == '0' and rig.stock.total_return == '-100.0'


@pytest.mark.parametrize('operation', ['profile', 'quote'])
@pytest.mark.parametrize('field,value', [('exchange', 'NYSE'), ('currency', 'EUR'), ('symbol', 'MSFT')])
def test_conflicting_metadata_rejects_before_publication_and_invalidates_price(rig, operation, field, value):
    from stock_tracker.exceptions import ProviderResponseError
    setattr(rig, operation, replace(getattr(rig, operation), **{field: value}))
    before = (rig.stock.name, rig.stock.exchange, rig.stock.currency, rig.stock.market_cap, rig.stock._position)
    with pytest.raises(ProviderResponseError) as caught:
        getattr(rig.stock, 'get_stock_info' if operation == 'profile' else 'get_realtime_price')()
    assert caught.value.field == field
    assert (rig.stock.name, rig.stock.exchange, rig.stock.currency, rig.stock.market_cap, rig.stock._position) == before
    assert rig.stock.current_price is None and rig.stock.total_return == '-'
    assert rig.stock._snapshot.market_value is None


def test_quote_absent_metadata_and_unknown_currency_remain_explicit(rig):
    rig.stock.get_realtime_price()
    assert rig.stock.name == 'Old company' and rig.stock.exchange == 'NASDAQ' and rig.stock.currency == 'USD'
    assert rig.stock.current_price == '80' and rig.stock.total_return == '-20.0'
    rig.stock.exchange = rig.stock.currency = None
    rig.stock.calculate_return()
    rig.stock.get_realtime_price()
    assert rig.stock.exchange == rig.stock.currency == 'N/A' and rig.stock._position.stock.exchange is None
    assert rig.calls == [('quote', 'AAPL')] * 2


@pytest.mark.parametrize('operation,method', [('profile', 'get_stock_info'), ('quote', 'get_realtime_price'),
                                            ('periods', 'get_price_over_time')])
@pytest.mark.parametrize('name', ERRORS)
def test_typed_facade_failures_invalidate_relevant_values_preserve_metadata_and_holdings(rig, operation, method, name):
    import stock_tracker.exceptions as errors
    rig.failing, rig.failure = operation, getattr(errors, name)()
    before = (rig.stock.name, rig.stock.exchange, rig.stock.currency, rig.stock.market_cap, rig.stock._position)
    with pytest.raises(getattr(errors, name)):
        getattr(rig.stock, method)()
    assert (rig.stock.name, rig.stock.exchange, rig.stock.currency, rig.stock.market_cap, rig.stock._position) == before
    if operation == 'periods':
        assert all(getattr(rig.stock, field) == 'N/A' for field in FIELDS)
        assert rig.stock.current_price == '120' and rig.stock.total_return == '20.0'
    else:
        assert rig.stock.current_price is None and rig.stock.total_return == '-'


def test_summary_maps_complete_candidate_without_unit_conversion(rig):
    rig.stock.get_price_over_time()
    assert [getattr(rig.stock, field) for field in FIELDS] == ['12.34', '-1.24', '0', 'N/A', '6', '7', '8', '9']
    assert rig.calls == [('periods', 'AAPL')]


@pytest.mark.parametrize('method', ['get_stock_info', 'get_realtime_price', 'get_price_over_time'])
def test_configuration_failure_and_programming_failure_are_distinct(rig, method):
    from config import ConfigurationError
    rig.failing, rig.failure = 'factory', RuntimeError('programming')
    before = dict(rig.stock.__dict__)
    with pytest.raises(RuntimeError):
        getattr(rig.stock, method)()
    assert rig.stock.__dict__ == before
    rig.failure = ConfigurationError('Set FMP_API_KEY in your environment or local .env before making requests.')
    with pytest.raises(ConfigurationError):
        getattr(rig.stock, method)()
    if method == 'get_price_over_time':
        assert all(getattr(rig.stock, field) == 'N/A' for field in FIELDS)
    else:
        assert rig.stock.current_price is None


@pytest.fixture(params=['menu_watchlist.py', 'daniils_stock_method.py'])
def cli(request, rig, monkeypatch):
    monkeypatch.setenv('FMP_API_KEY', 'synthetic-integration-runtime')
    module = runpy.run_path(str(ROOT / request.param), run_name='provider_integration_test')
    return module, rig


@pytest.mark.parametrize('stage', ['resolve', 'profile', 'periods'])
@pytest.mark.parametrize('name', ERRORS)
def test_cli_failed_add_renders_safe_category_and_never_adds_or_saves(cli, stage, name, tmp_path, caplog):
    import stock_tracker.exceptions as errors
    module, rig = cli
    csv = tmp_path / 'list_of_valid_tickers.csv'
    csv.write_bytes(b'AAPL\n')
    rig.failing, rig.failure = stage, getattr(errors, name)()
    result = CliRunner().invoke(module['app'], ['add-stock'], input='aapl\n')
    assert result.exit_code == 1 and str(rig.failure) in result.output
    assert 'Succesfully' not in result.output and 'Invalid ticker. Try again.' not in result.output
    assert module['current_watchlist'].stocks == []
    assert not (tmp_path / module['WATCHLIST_FILE']).exists() and csv.read_bytes() == b'AAPL\n'
    assert 'synthetic-' not in result.output + caplog.text
    assert [name for name, _ in rig.calls] == ['resolve', 'profile', 'periods'][:['resolve', 'profile', 'periods'].index(stage) + 1]


@pytest.mark.parametrize('stage', ['profile', 'periods'])
@pytest.mark.parametrize('name', ERRORS)
def test_cli_failed_refresh_keeps_saved_file_and_invalidates_in_memory(cli, stage, name, tmp_path):
    import stock_tracker.exceptions as errors
    module, rig = cli
    module['current_watchlist'].add_stock(rig.stock)
    module['save_watchlist'](module['current_watchlist'])
    path = tmp_path / module['WATCHLIST_FILE']
    before = path.read_bytes()
    rig.failing, rig.failure = stage, getattr(errors, name)()
    result = CliRunner().invoke(module['app'], ['refresh'])
    assert result.exit_code == 1 and str(rig.failure) in result.output and 'Succesfully' not in result.output
    assert path.read_bytes() == before
    if stage == 'profile':
        assert rig.stock.current_price is None and rig.stock.total_return == '-'
    else:
        assert rig.stock.current_price == '130' and all(getattr(rig.stock, field) == 'N/A' for field in FIELDS)
    assert [name for name, _ in rig.calls] == ['profile', 'periods'][:1 if stage == 'profile' else 2]


def test_restored_runtime_key_factory_error_after_valid_cli_precheck(cli, monkeypatch, tmp_path):
    module, rig = cli
    monkeypatch.setenv('FMP_API_KEY', '')
    restored = pickle.loads(pickle.dumps(rig.stock))
    assert restored.API_KEY == '' and module['API_KEY'] == 'synthetic-integration-runtime'
    module['current_watchlist'].add_stock(restored)
    # The module captures its valid key, while the restored object has a blank key.
    from config import ConfigurationError
    from stock_tracker.compatibility import stock_operations
    with pytest.MonkeyPatch.context() as local:
        local.setattr(stock_operations.provider_factory, 'create_market_data_provider', rig.real_factory)
        result = CliRunner().invoke(module['app'], ['refresh'])
    assert result.exit_code == 1 and 'Set FMP_API_KEY' in result.output
    assert restored.current_price is None and not (tmp_path / module['WATCHLIST_FILE']).exists()
    assert not isinstance(result.exception, ConfigurationError)


def test_cli_explicit_null_price_add_succeeds_without_fabricated_return(cli, tmp_path):
    module, rig = cli
    rig.profile = replace(rig.profile, price=None)
    result = CliRunner().invoke(module['app'], ['add-stock'], input='aapl\n0.25\n100\n')
    assert result.exit_code == 0 and 'Succesfully added' in result.output
    stock = module['current_watchlist'].stocks[0]
    assert stock.current_price is None and stock.total_return == '-'
    assert stock._position.quantity == Decimal('0.25') and stock._snapshot.market_value is None
    path = tmp_path / module['WATCHLIST_FILE']
    assert path.exists() and b'synthetic-integration-runtime' not in path.read_bytes()
    assert [name for name, _ in rig.calls] == ['resolve', 'profile', 'periods']


@pytest.mark.parametrize('command,stage', [('add-stock', 'resolve'), ('refresh', 'profile')])
def test_cli_programming_exception_propagates_without_saving(cli, command, stage, tmp_path):
    module, rig = cli
    rig.failing, rig.failure = stage, RuntimeError('programming')
    if command == 'refresh':
        module['current_watchlist'].add_stock(rig.stock)
    before = dict(rig.stock.__dict__)
    result = CliRunner().invoke(module['app'], [command], input='aapl\n')
    assert isinstance(result.exception, RuntimeError)
    assert rig.stock.__dict__ == before and not (tmp_path / module['WATCHLIST_FILE']).exists()


def test_failed_add_preserves_existing_watchlist_and_saved_bytes(cli, tmp_path):
    from stock_tracker.exceptions import ProviderUnavailableError
    module, rig = cli
    module['current_watchlist'].add_stock(rig.stock)
    module['save_watchlist'](module['current_watchlist'])
    path = tmp_path / module['WATCHLIST_FILE']
    before, state = path.read_bytes(), dict(rig.stock.__dict__)
    rig.failing, rig.failure = 'profile', ProviderUnavailableError()
    result = CliRunner().invoke(module['app'], ['add-stock'], input='msft\n')
    assert result.exit_code == 1 and str(rig.failure) in result.output
    assert module['current_watchlist'].stocks == [rig.stock] and rig.stock.__dict__ == state
    assert path.read_bytes() == before and rig.calls == [('resolve', 'MSFT'), ('profile', 'MSFT')]


def test_partial_two_stock_refresh_preserves_saved_file_and_order(cli, tmp_path):
    from stock import Stock
    from stock_tracker.exceptions import ProviderUnavailableError
    module, rig = cli
    dummy = 'synthetic-integration-runtime'
    second = Stock('MSFT', dummy, name='Old second', exchange='NASDAQ', currency='USD',
                   current_price='120', amount_owned='3', cost_basis='100')
    module['current_watchlist'].stocks[:] = [rig.stock, second]
    module['save_watchlist'](module['current_watchlist'])
    path = tmp_path / module['WATCHLIST_FILE']
    before = path.read_bytes()
    rig.failing, rig.failure, rig.fail_symbol = 'profile', ProviderUnavailableError(), 'MSFT'
    result = CliRunner().invoke(module['app'], ['refresh'])
    assert result.exit_code == 1 and path.read_bytes() == before
    assert module['current_watchlist'].stocks == [rig.stock, second]
    assert rig.stock.current_price == '130' and rig.stock.name == 'New company'
    assert second.current_price is None and second.total_return == '-' and second.name == 'Old second'
    assert second._position.quantity == Decimal(3) and second._position.stock.exchange == 'NASDAQ'
    assert rig.calls == [('profile', 'AAPL'), ('periods', 'AAPL'), ('profile', 'MSFT')]


def test_wrong_summary_identity_invalidates_all_periods_without_changing_price(rig):
    from stock_tracker.exceptions import ProviderResponseError
    rig.periods = replace(rig.periods, symbol='MSFT')
    with pytest.raises(ProviderResponseError, match='symbol'):
        rig.stock.get_price_over_time()
    assert all(getattr(rig.stock, field) == 'N/A' for field in FIELDS)
    assert rig.stock.current_price == '120' and rig.stock.total_return == '20.0'


def test_scratch_entrypoint_reaches_typed_profile_facade(rig, monkeypatch):
    monkeypatch.setenv('FMP_API_KEY', 'synthetic-scratch-runtime')
    rig.profile = replace(rig.profile, symbol='AMD')
    scratch = runpy.run_path(str(ROOT / 'test.py'), run_name='scratch_integration_test')
    scratch['main']()
    assert rig.calls == [('profile', 'AMD')] and rig.keys == ['synthetic-scratch-runtime']
