"""Legacy root facade contracts using real domain arithmetic and synthetic state."""

from datetime import datetime, timezone
from decimal import Decimal
import inspect
import pickle
from types import SimpleNamespace

import pytest


@pytest.fixture
def stock():
    from stock import Stock

    credential = "synthetic-runtime"
    return Stock("AAPL", credential, current_price="120")


@pytest.mark.parametrize("value,expected", [
    (Decimal("0.123456789123456789"), Decimal("0.123456789123456789")),
    (" 1.25e2 ", Decimal("125")), (".25", Decimal("0.25")),
    ("-2", Decimal("-2")), (2, Decimal("2")), (0.25, Decimal("0.25")),
])
def test_boundary_conversion_is_explicit(value, expected):
    from stock_tracker.compatibility.numeric import to_decimal

    assert to_decimal(value, "quantity") == expected
    if isinstance(value, Decimal):
        assert to_decimal(value, "quantity") is value


@pytest.mark.parametrize("invalid", [
    True, None, "", "1_0", "$10", "10%", "NaN", "Infinity", "bad-private-value",
    float("nan"), float("inf"), Decimal("sNaN"), Decimal("-Infinity"), object(),
])
def test_boundary_conversion_rejects_unsafe_or_decorated_inputs(invalid):
    from stock_tracker.compatibility.numeric import to_decimal
    from stock_tracker.domain import DomainValidationError

    with pytest.raises(DomainValidationError) as caught:
        to_decimal(invalid, "quantity")
    assert str(caught.value) == "quantity must be a finite plain decimal number."


def test_constructor_order_defaults_and_optional_fields():
    from stock import Stock

    assert list(inspect.signature(Stock).parameters) == [
        "ticker_symbol", "API_KEY", "name", "sector", "country", "exchange",
        "current_price", "market_cap", "price_1d", "price_5d", "price_30d",
        "price_3m", "price_6m", "price_1y", "price_3y", "price_5y", "currency",
        "amount_owned", "cost_basis", "total_return",
    ]
    credential = "synthetic-runtime"
    values = ["AAPL", credential, "Example", "Tech", "US", "NASDAQ", "120", "1.000B",
              "1", "2", "3", "4", "5", "6", "7", "8", "USD", "10", "100", "999"]
    stock = Stock(*values)
    assert stock.API_KEY == credential
    assert (stock.name, stock.sector, stock.country, stock.exchange, stock.currency) == (
        "Example", "Tech", "US", "NASDAQ", "USD",
    )
    assert [getattr(stock, field) for field in (
        "price_1d", "price_5d", "price_30d", "price_3m", "price_6m", "price_1y",
        "price_3y", "price_5y",
    )] == [str(value) for value in range(1, 9)]
    assert stock.total_return == "20.0"  # The supplied stale return is never authoritative.
    unowned = Stock(ticker_symbol="AAPL", API_KEY=credential)
    assert (unowned.amount_owned, unowned.cost_basis, unowned.total_return) == ("0", "-", "-")
    assert unowned._position is None
    assert credential not in repr(stock)
    assert "API_KEY" not in repr(stock)


def test_fractional_ownership_and_presentation_do_not_mutate_domain(stock):
    from watch_list import Watch_list

    stock.set_owned_data("0.123456789123456789", "100.123456789123456789")
    position, snapshot = stock._position, stock._snapshot
    assert position.quantity == Decimal("0.123456789123456789")
    assert position.average_cost == Decimal("100.123456789123456789")
    assert stock.cost_basis == "100.123456789123456789"
    assert isinstance(snapshot.unrealized_return, Decimal)
    Watch_list.wrap_percent(stock.total_return)
    stock.format_mcap(1_000_000_000)
    assert stock._position is position and stock._snapshot is snapshot


@pytest.mark.parametrize("quantity,cost", [
    ("-1", "200"), ("2", "-1"), ("NaN", "200"), ("2", "bad-private-value"),
])
def test_rejected_ownership_updates_are_atomic(stock, quantity, cost):
    from stock_tracker.domain import DomainValidationError

    stock.set_owned_data("10", "100")
    before = stock.__getstate__(), stock._position, stock._snapshot
    with pytest.raises(DomainValidationError):
        stock.set_owned_data(quantity, cost)
    assert stock.__getstate__() == before[0]
    assert stock._position is before[1] and stock._snapshot is before[2]


@pytest.mark.parametrize("invalid", ["-1", "NaN", "N/A ", True, float("inf")])
def test_rejected_quote_preserves_previous_values(stock, invalid):
    from stock_tracker.domain import DomainValidationError

    stock.set_owned_data("10", "100")
    before = stock.current_price, stock._quote, stock._snapshot
    with pytest.raises(DomainValidationError):
        stock.current_price = invalid
    assert (stock.current_price, stock._quote, stock._snapshot) == before


def test_valid_missing_zero_price_and_zero_basis_transitions(stock):
    stock.set_owned_data("10", "100")
    assert stock.total_return == "20.0"
    stock.current_price = "N/A"
    stock.calculate_return()
    assert stock.total_return == "-" and stock._snapshot.market_value is None
    stock.current_price = "0"
    assert stock.total_return == "-100.0" and stock._snapshot.market_value == Decimal("0")
    stock.current_price = "120"
    stock.set_owned_data("10", "0")
    assert stock.total_return == "-" and stock._snapshot.market_value == Decimal("1200")
    stock.set_owned_data("0", "100")
    assert stock._snapshot.market_value == Decimal("0") and stock.total_return == "-"
    stock.current_price = None
    assert stock._snapshot.market_value is None


@pytest.mark.parametrize("missing", [None, "N/A"])
def test_unknown_identity_sentinels_never_become_known_exchange(missing):
    from stock import Stock

    stock = Stock("AAPL", None, name=missing, exchange=missing, amount_owned="1", cost_basis="2")
    assert stock._position.stock.name is None
    assert stock._position.stock.exchange is None


def test_property_updates_and_return_assignment_use_domain(stock):
    stock.set_owned_data("10", "100")
    stock.cost_basis = "120"
    stock.amount_owned = "0.25"
    stock.total_return = "999"
    assert stock._position.quantity == Decimal("0.25")
    assert stock._position.average_cost == Decimal("120")
    assert stock.total_return == "0.0"


def test_provider_request_order_schema_mapping_and_refresh(monkeypatch, stock):
    from stock_tracker.compatibility import stock_operations
    from stock_tracker.providers.models import CompanyProfile, PeriodChanges, Quote
    from stock_tracker.exceptions import MarketDataUnavailableError
    from watch_list import Watch_list

    calls = []
    received = datetime(2020, 1, 1, tzinfo=timezone.utc)
    profiles = [CompanyProfile('AAPL', 'Example', 'NASDAQ', 'USD', 'Tech', 'US', Decimal(120), Decimal(10**9), None, received),
                MarketDataUnavailableError()]
    def profile(symbol):
        calls.append('profile')
        value = profiles.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value
    def quote(symbol):
        calls.append('quote')
        return Quote(symbol, Decimal(80), 'NASDAQ', None, None, received)
    def periods(symbol):
        calls.append('periods')
        return PeriodChanges(symbol, *(Decimal(i) for i in range(1, 9)), None, received)
    provider = SimpleNamespace(get_company_profile=profile, get_quote=quote, get_period_changes=periods)
    def factory(key):
        assert key == 'synthetic-runtime'
        return provider
    monkeypatch.setattr(stock_operations.provider_factory, 'create_market_data_provider', factory)
    stock.set_owned_data("10", "100")
    watchlist = Watch_list("Example", [stock])
    watchlist.refresh_stocks()
    assert stock.total_return == "20.0"
    assert stock.market_cap == "1.000B"
    assert stock.price_5y == "8"
    assert stock._position.stock.exchange == "NASDAQ"
    stock.get_realtime_price()
    assert stock.total_return == "-20.0"
    with pytest.raises(MarketDataUnavailableError):
        watchlist.refresh_stocks()
    assert stock.current_price is None and stock.total_return == "-"
    assert stock._position.stock.exchange == 'NASDAQ' and stock.name == 'Example'
    assert calls == ['profile', 'periods', 'quote', 'profile']


def test_legacy_chart_delegates_with_fixed_clock(monkeypatch, stock):
    from stock_tracker.compatibility import presentation

    class FixedDatetime:
        @staticmethod
        def today():
            return datetime(2020, 1, 2)

    calls = {}
    monkeypatch.setattr(presentation, "datetime", FixedDatetime)
    for name in ("figure", "title", "xlabel", "ylabel", "grid", "legend", "show"):
        monkeypatch.setattr(presentation.plt, name, lambda *a, **kw: None)
    monkeypatch.setattr(presentation.plt, "plot", lambda dates, prices, **kw: calls.update(
        dates=dates, prices=prices, kwargs=kw,
    ))
    for name in ("price_1d", "price_5d", "price_30d", "price_3m", "price_6m", "price_1y", "price_3y", "price_5y"):
        setattr(stock, name, "20")
    stock.graph_performance()
    assert calls["dates"][0] == datetime(2020, 1, 2)
    assert calls["prices"] == (120.0,) + (100.0,) * 8
    assert stock._position is None


@pytest.mark.parametrize("value,expected", [(None, "-"), ("-", "-"), ("N/A", "-"),
                                            ("20.0", "[green]20.0%[/]"), ("-20.0", "[red]-20.0%[/]")])
def test_percent_sentinels_and_colors(value, expected):
    from watch_list import Watch_list

    assert Watch_list.wrap_percent(value) == expected


def test_new_pickle_state_excludes_credentials_and_unknown_handles(monkeypatch, tmp_path, stock):
    from config import Configuration
    from watch_list import Watch_list

    stock.set_owned_data("0.25", "100.123456789")
    stock.client = SimpleNamespace(secret=stock.API_KEY)
    stock.configuration = Configuration(stock.API_KEY)
    before = stock.__getstate__()
    assert "API_KEY" not in before and "_runtime_key" not in before
    assert not any(isinstance(value, Configuration) for value in before.values())
    path = tmp_path / "synthetic.pkl"
    path.write_bytes(pickle.dumps(Watch_list("Example", [stock])))
    assert stock.API_KEY.encode() not in path.read_bytes()
    assert b"Configuration" not in path.read_bytes() and b"client" not in path.read_bytes()
    monkeypatch.setenv("FMP_API_KEY", "synthetic-new-runtime")
    restored = pickle.loads(path.read_bytes())
    assert restored.name == "Example"
    assert restored.stocks[0].__getstate__() == before
    assert restored.stocks[0].API_KEY == "synthetic-new-runtime"
    assert restored.stocks[0]._position.quantity == Decimal("0.25")
    assert restored.stocks[0]._position.average_cost == Decimal("100.123456789")


def test_old_root_class_pickle_preserves_holdings_ignores_saved_key(monkeypatch, tmp_path):
    import stock as root
    from watch_list import Watch_list

    facade = root.Stock
    legacy_class = type("Stock", (), {"__module__": "stock"})
    legacy = legacy_class()
    saved_credential = "synthetic-old-saved"
    legacy.__dict__.update(ticker_symbol="AAPL", API_KEY=saved_credential,
                           name="Example", exchange="N/A", current_price="120",
                           amount_owned="0.25", cost_basis="100", total_return="999")
    with monkeypatch.context() as local:
        local.setattr(root, "Stock", legacy_class)
        encoded = pickle.dumps(Watch_list("Legacy", [legacy, legacy]))
    path = tmp_path / "synthetic-legacy.pkl"
    path.write_bytes(encoded)
    monkeypatch.setenv("FMP_API_KEY", "synthetic-current")
    monkeypatch.setenv("MY_API_KEY", "synthetic-fallback")
    restored = pickle.loads(path.read_bytes())
    item = restored.stocks[0]
    assert isinstance(item, facade) and restored.stocks[1] is item
    assert restored.name == "Legacy"
    assert item.amount_owned == "0.25" and item.cost_basis == "100"
    assert item.total_return == "20.0" and item._position.stock.exchange is None
    assert item.API_KEY == "synthetic-current"
    assert saved_credential not in repr(item)
    assert saved_credential.encode() not in pickle.dumps(restored)


@pytest.mark.parametrize("canonical", [None, "", " \t"])
def test_restore_without_usable_runtime_key_is_local_only(monkeypatch, stock, canonical):
    from config import ConfigurationError
    from stock_tracker.compatibility import stock_operations

    state = stock.__getstate__()
    state["API_KEY"] = "synthetic-saved"
    if canonical is not None:
        monkeypatch.setenv("FMP_API_KEY", canonical)
        monkeypatch.setenv("MY_API_KEY", "synthetic-fallback")
    stock.__setstate__(state)
    assert stock.API_KEY == canonical
    assert stock.current_price == "120" and stock.total_return == "-"
    monkeypatch.setattr(stock_operations.provider_factory.UrllibHttpTransport, 'get', lambda *a, **kw: pytest.fail('transport reached'))
    with pytest.raises(ConfigurationError, match="Set FMP_API_KEY"):
        stock.get_stock_info()
    assert stock.current_price is None


def test_restore_uses_legacy_config_fallback_only_when_canonical_absent(monkeypatch, stock):
    monkeypatch.setenv("MY_API_KEY", "synthetic-fallback")
    stock.__setstate__(stock.__getstate__())
    assert stock.API_KEY == "synthetic-fallback"


@pytest.mark.parametrize("cost", ["-", None, "bad-private-value"])
def test_failed_legacy_restoration_does_not_replace_existing_holdings(stock, cost):
    from stock_tracker.domain import DomainValidationError

    stock.set_owned_data("10", "100")
    before = dict(stock.__dict__)
    state = stock.__getstate__() | {"amount_owned": "2", "cost_basis": cost}
    with pytest.raises(DomainValidationError):
        stock.__setstate__(state)
    assert stock.__dict__ == before


@pytest.mark.parametrize("method", ["get_stock_info", "get_realtime_price"])
def test_provider_null_quote_is_unavailable_without_display_crash(monkeypatch, stock, method, capsys):
    from stock_tracker.compatibility import stock_operations
    from stock_tracker.providers.models import CompanyProfile, Quote
    from watch_list import Watch_list

    stock.set_owned_data("10", "100")
    monkeypatch.setenv('COLUMNS', '300')
    stamp = datetime(2020, 1, 1, tzinfo=timezone.utc)
    provider = SimpleNamespace(get_company_profile=lambda symbol: CompanyProfile(symbol, 'Example', 'NASDAQ', 'USD', 'Tech', 'US', None, Decimal(10**9), None, stamp),
                               get_quote=lambda symbol: Quote(symbol, None, None, None, None, stamp))
    monkeypatch.setattr(stock_operations.provider_factory, 'create_market_data_provider', lambda key: provider)
    getattr(stock, method)()
    stock.calculate_return()
    assert stock.current_price is None and stock.total_return == "-"
    assert stock._snapshot.market_value is None
    Watch_list("Example", [stock]).show_stocks()
    assert "AAPL" in capsys.readouterr().out


def test_runtime_property_rebinding_reaches_real_provider_boundary(monkeypatch, stock):
    from stock_tracker.compatibility import stock_operations
    from stock_tracker.providers.transport import HttpResponse
    from stock_tracker.exceptions import MarketDataUnavailableError

    replacement = "synthetic-replacement"
    stock.API_KEY = replacement
    calls = []
    def transport(self, url, *, headers, timeout_seconds):
        calls.append((url, headers))
        return HttpResponse(200, {}, b'[]')
    monkeypatch.setattr(stock_operations.provider_factory.UrllibHttpTransport, 'get', transport)
    with pytest.raises(MarketDataUnavailableError):
        stock.get_realtime_price()
    assert calls[0][1] == {'apikey': replacement} and replacement not in calls[0][0]
    assert replacement not in repr(stock)
    assert replacement.encode() not in pickle.dumps(stock)
