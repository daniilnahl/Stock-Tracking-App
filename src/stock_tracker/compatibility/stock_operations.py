"""Legacy facade mappings over typed provider capabilities, without HTTP schemas."""

from config import ConfigurationError
from stock_tracker.domain import Position, Stock as Security, position_snapshot
from stock_tracker.exceptions import ProviderResponseError, StockTrackerError
from stock_tracker.providers import factory as provider_factory
from . import presentation


_PERIOD_FIELDS = (('price_1d', 'day_1'), ('price_5d', 'day_5'), ('price_30d', 'month_1'),
                  ('price_3m', 'month_3'), ('price_6m', 'month_6'), ('price_1y', 'year_1'),
                  ('price_3y', 'year_3'), ('price_5y', 'year_5'))


def _known(value):
    return None if value in (None, 'N/A') else value


def _identity_metadata(self, result):
    if result.symbol != self.ticker_symbol.strip().upper():
        raise ProviderResponseError(field='symbol')
    changes = {}
    for field in ('exchange', 'currency'):
        existing, returned = _known(getattr(self, field)), getattr(result, field)
        if existing is not None and returned is not None and existing != returned:
            raise ProviderResponseError(field=field)
        changes[field] = returned if returned is not None else existing or 'N/A'
    return changes


def _publish_price(self, price, metadata):
    # Validate the entire candidate with unchanged domain arithmetic before any
    # metadata/price publication. Never reinterpret known holding identity.
    security = Security(self.ticker_symbol, _known(metadata.get('name', self.name)),
                        _known(metadata.get('exchange', self.exchange)))
    position = None if self._position is None else Position(
        security, self._position.quantity, self._position.average_cost,
    )
    snapshot = None if position is None else position_snapshot(position, price)
    changes = dict(metadata, _position=position, _snapshot=snapshot, _quote=price,
                   _price_text=None if price is None else str(price))
    self.__dict__.update(changes)


def get_stock_info(self):
    try:
        profile = provider_factory.create_market_data_provider(self.API_KEY).get_company_profile(self.ticker_symbol)
        metadata = _identity_metadata(self, profile)
        metadata.update(name=profile.name, sector=profile.sector or 'N/A', country=profile.country or 'N/A',
                        market_cap='N/A' if profile.market_cap is None else presentation.format_mcap(profile.market_cap))
        _publish_price(self, profile.price, metadata)
    except (StockTrackerError, ConfigurationError):
        self.current_price = None
        raise


def get_realtime_price(self):
    try:
        quote = provider_factory.create_market_data_provider(self.API_KEY).get_quote(self.ticker_symbol)
        _publish_price(self, quote.price, _identity_metadata(self, quote))
    except (StockTrackerError, ConfigurationError):
        self.current_price = None
        raise


def get_price_over_time(self):
    try:
        result = provider_factory.create_market_data_provider(self.API_KEY).get_period_changes(self.ticker_symbol)
        if result.symbol != self.ticker_symbol.strip().upper():
            raise ProviderResponseError(field='symbol')
        changes = {target: 'N/A' if getattr(result, field) is None else
                   format(getattr(result, field), '.2f').rstrip('0').rstrip('.')
                   for target, field in _PERIOD_FIELDS}
        self.__dict__.update(changes)
    except (StockTrackerError, ConfigurationError):
        for target, _ in _PERIOD_FIELDS:
            setattr(self, target, 'N/A')
        raise
