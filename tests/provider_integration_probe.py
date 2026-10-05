"""Fresh installed-wheel provider/facade integration; invoked only by tests.

Synthetic Stable fields follow accepted ADR-0007 samples inspected 2026-10-04.
Real network/TLS paths are independently denied before application imports.
"""

from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import pickle
import socket
import ssl
import sys
from unittest.mock import patch
import urllib.request
from urllib.parse import parse_qs, urlsplit

import certifi


class ForbiddenIO(BaseException):
    """Cannot be swallowed by legacy broad Exception handlers."""


def denied(*args, **kwargs):
    raise ForbiddenIO('Real provider IO denied')


def expect_denied(call):
    try:
        call()
    except ForbiddenIO:
        return
    raise AssertionError('Provider guard did not enforce denial')


target = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(target))
guards = [patch.object(urllib.request, 'urlopen', denied),
          patch.object(urllib.request.OpenerDirector, 'open', denied),
          patch.object(socket, 'getaddrinfo', denied), patch.object(socket, 'create_connection', denied),
          patch.object(socket.socket, 'connect', denied), patch.object(socket.socket, 'connect_ex', denied),
          patch.object(socket.socket, 'sendto', denied), patch.object(ssl, 'create_default_context', denied),
          patch.object(certifi, 'where', denied)]
for guard in guards:
    guard.start()
# Exercise cached modules and bound-method paths as well as module entry points.
expect_denied(lambda: urllib.request.urlopen('https://example.invalid/'))
expect_denied(lambda: urllib.request.build_opener().open('https://example.invalid/'))
expect_denied(lambda: socket.getaddrinfo('example.invalid', 443))
expect_denied(lambda: socket.create_connection(('example.invalid', 443)))
with socket.socket() as connection:
    expect_denied(lambda: connection.connect(('127.0.0.1', 9)))
    expect_denied(lambda: connection.connect_ex(('127.0.0.1', 9)))
    expect_denied(lambda: connection.sendto(b'x', ('127.0.0.1', 9)))
expect_denied(ssl.create_default_context)
expect_denied(certifi.where)

def import_application():
    # Import only after independent guard enforcement; no lint suppression.
    from stock import Stock
    from stock_tracker.providers import factory
    from stock_tracker.providers.models import CompanyProfile, InstrumentIdentity, PeriodChanges, Quote
    from stock_tracker.providers.transport import HttpResponse
    from utils.utility_module import check_ticker
    return Stock, factory, CompanyProfile, InstrumentIdentity, PeriodChanges, Quote, HttpResponse, check_ticker


Stock, factory, CompanyProfile, InstrumentIdentity, PeriodChanges, Quote, HttpResponse, check_ticker = import_application()


credential = 'synthetic-installed-provider-fixture'
provider = factory.create_market_data_provider(credential)  # Real approved composition, no IO.
received = datetime(2020, 1, 2, tzinfo=timezone.utc)
requests = []


class FixtureHTTP:
    def get(self, url, *, headers, timeout_seconds):
        assert headers == {'apikey': credential} and timeout_seconds == 10.0
        assert credential not in url
        route = urlsplit(url).path.removeprefix('/stable/')
        query = parse_qs(urlsplit(url).query)
        requests.append(route)
        if route == 'search-symbol':
            assert query == {'query': ['AAPL'], 'limit': ['100'], 'exchange': ['NASDAQ']}
            rows = [{'symbol': 'AAPL', 'exchange': 'NASDAQ', 'name': 'Fictional company', 'currency': 'USD'}]
        else:
            assert query == {'symbol': ['AAPL']}
            if route == 'quote':
                rows = [{'symbol': 'AAPL', 'price': 130, 'exchange': 'NASDAQ', 'timestamp': 1577836800}]
            elif route == 'profile':
                rows = [{'symbol': 'AAPL', 'companyName': 'Fictional company', 'price': 125,
                         'marketCap': 10**9, 'exchange': 'NASDAQ', 'currency': 'USD'}]
            elif route == 'stock-price-change':
                rows = [{'symbol': 'AAPL', '1D': -1.5, '5D': 0, '1M': 12.5}]
            else:
                raise AssertionError('Unexpected provider request')
        return HttpResponse(200, {}, json.dumps(rows).encode())


provider._transport = FixtureHTTP()
provider._clock = lambda: received
provider._monotonic = lambda: 0.0
provider._sleep = denied
provider._jitter = lambda upper: 0.0
identity = provider.resolve_symbol(' aapl ')
quote = provider.get_quote('AAPL')
profile = provider.get_company_profile('AAPL')
periods = provider.get_period_changes('AAPL')
assert isinstance(identity, InstrumentIdentity) and identity.exchange == 'NASDAQ'
assert isinstance(quote, Quote) and quote.price == Decimal(130) and quote.currency is None
assert quote.as_of == datetime(2020, 1, 1, tzinfo=timezone.utc) and quote.retrieved_at == received
assert isinstance(profile, CompanyProfile) and profile.price == Decimal(125) and profile.as_of is None
assert isinstance(periods, PeriodChanges) and periods.day_1 == Decimal('-1.5')
assert periods.day_5 == Decimal(0) and periods.month_1 == Decimal('12.5') and periods.year_5 is None
assert requests == ['search-symbol', 'quote', 'profile', 'stock-price-change']
assert credential not in repr(identity) + repr(quote) + repr(profile) + repr(periods) + repr(provider)


def create(key):
    assert key == credential
    return provider


requests.clear()
with patch.object(factory, 'create_market_data_provider', create):
    assert check_ticker('AAPL', credential) is True
    stock = Stock('AAPL', credential, name='Old company', exchange='NASDAQ', currency='USD',
                  current_price='120', amount_owned='2', cost_basis='100')
    stock.get_stock_info()
    assert stock.name == stock._position.stock.name == 'Fictional company'
    assert stock.current_price == '125' and stock.total_return == '25.0'
    stock.get_realtime_price()
    assert stock.current_price == '130' and stock.total_return == '30.0'
    stock.get_price_over_time()
    assert stock.price_1d == '-1.5' and stock.price_5d == '0'
    assert stock.price_30d == '12.5' and stock.price_5y == 'N/A'
    assert stock._position.quantity == Decimal(2) and stock._position.average_cost == Decimal(100)
    assert credential.encode() not in pickle.dumps(stock)
    assert not {'API_KEY', '_runtime_key', 'provider', 'client'} & stock.__getstate__().keys()
assert requests == ['search-symbol', 'profile', 'quote', 'stock-price-change']
for name, module in tuple(sys.modules.items()):
    if name == 'stock' or name == 'config' or name == 'utils' or name.startswith('utils.') or name == 'stock_tracker' or name.startswith('stock_tracker.'):
        if module.__file__ is None:
            assert name == 'utils'
            # Namespace packages can also contain the canonical environment's
            # installed utils directory; exercised file modules must use target.
            assert Path(next(iter(module.__path__))).resolve() == target / 'utils'
        else:
            assert Path(module.__file__).resolve().is_relative_to(target), name
