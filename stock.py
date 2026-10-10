"""Root-class compatibility facade; ownership arithmetic lives in pure domain."""

from datetime import date
from config import load_configuration
from stock_tracker.domain import DomainValidationError, Position, Stock as Security, position_snapshot
from stock_tracker.compatibility.numeric import to_decimal
from stock_tracker.compatibility import presentation, stock_operations
from stock_tracker.compatibility import history_operations
from stock_tracker.providers.models import PriceBar


class Stock:
    """Preserve legacy fields/methods without persisting runtime credentials."""

    _STATE_FIELDS = (
        "ticker_symbol", "name", "sector", "country", "exchange", "current_price",
        "market_cap", "price_1d", "price_5d", "price_30d", "price_3m", "price_6m",
        "price_1y", "price_3y", "price_5y", "currency", "amount_owned", "cost_basis",
        "total_return",
    )

    def __init__(
        self, ticker_symbol: str, API_KEY: str | None,
        name: str | None = None, sector: str | None = None,
        country: str | None = None, exchange: str | None = None,
        current_price: str | None = None, market_cap: str | None = None,
        price_1d: str | None = None, price_5d: str | None = None,
        price_30d: str | None = None, price_3m: str | None = None,
        price_6m: str | None = None, price_1y: str | None = None,
        price_3y: str | None = None, price_5y: str | None = None,
        currency: str | None = None, amount_owned: str = "0",
        cost_basis: str = "-", total_return: str = "-",
    ) -> None:
        self.ticker_symbol = ticker_symbol
        self.API_KEY = API_KEY
        self.name, self.sector, self.country, self.exchange = name, sector, country, exchange
        self.market_cap, self.currency = market_cap, currency
        self.price_1d, self.price_5d, self.price_30d = price_1d, price_5d, price_30d
        self.price_3m, self.price_6m, self.price_1y = price_3m, price_6m, price_1y
        self.price_3y, self.price_5y = price_3y, price_5y
        self._position = None
        self._snapshot = None
        self.current_price = current_price
        # total_return is accepted for call compatibility, never trusted as arithmetic.
        self.set_owned_data(amount_owned, cost_basis)

    def __repr__(self) -> str:
        return f"Stock(ticker_symbol={self.ticker_symbol!r})"

    @property
    def API_KEY(self) -> str | None:
        return self._runtime_key

    @API_KEY.setter
    def API_KEY(self, value: str | None) -> None:
        self._runtime_key = value

    def _security(self) -> Security:
        name = None if self.name in (None, "N/A") else self.name
        exchange = None if self.exchange in (None, "N/A") else self.exchange
        return Security(self.ticker_symbol, name, exchange)

    @property
    def current_price(self) -> str | None:
        return self._price_text

    @current_price.setter
    def current_price(self, value) -> None:
        missing = value is None or value == "N/A"
        quote = None if missing else to_decimal(value, "current_price")
        if quote is not None and quote < 0:
            raise DomainValidationError("current_price must be a finite nonnegative Decimal or None.")
        snapshot = position_snapshot(self._position, quote) if self._position is not None else None
        self._quote = quote
        self._price_text = value if missing else str(quote)
        self._snapshot = snapshot

    @property
    def amount_owned(self) -> str:
        return str(self._position.quantity) if self._position is not None else str(self._unowned_quantity)

    @amount_owned.setter
    def amount_owned(self, value) -> None:
        self.set_owned_data(value, self.cost_basis)

    @property
    def cost_basis(self) -> str:
        return str(self._position.average_cost) if self._position is not None else "-"

    @cost_basis.setter
    def cost_basis(self, value) -> None:
        self.set_owned_data(self.amount_owned, value)

    @property
    def total_return(self) -> str:
        ratio = None if self._snapshot is None else self._snapshot.unrealized_return
        return presentation.format_return(ratio)

    @total_return.setter
    def total_return(self, value) -> None:
        self.calculate_return()

    def set_owned_data(self, amount_owned, cost_basis) -> None:
        quantity = to_decimal(amount_owned, "amount_owned")
        security = self._security()
        if cost_basis == "-" and quantity == 0:
            candidate = None
            snapshot = None
        else:
            average_cost = to_decimal(cost_basis, "cost_basis")
            candidate = Position(security, quantity, average_cost)
            snapshot = position_snapshot(candidate, self._quote)
        self._position, self._snapshot = candidate, snapshot
        self._unowned_quantity = quantity

    def calculate_return(self) -> None:
        # Rebuild identity after provider metadata changes; no saved return is reused.
        self.set_owned_data(self.amount_owned, self.cost_basis)

    def get_stock_info(self):
        return stock_operations.get_stock_info(self)

    def get_realtime_price(self):
        return stock_operations.get_realtime_price(self)

    def get_price_over_time(self):
        return stock_operations.get_price_over_time(self)

    def get_price_history(self, *, start: date | None = None, end: date | None = None) -> list[PriceBar]:
        return history_operations.get_price_history(self, start=start, end=end)

    def graph_performance(self, *, start: date | None = None, end: date | None = None):
        return presentation.graph_performance(self, start=start, end=end)

    @staticmethod
    def format_mcap(mcap: float):
        return presentation.format_mcap(mcap)

    def __getstate__(self) -> dict:
        return {field: getattr(self, field) for field in self._STATE_FIELDS}

    def __setstate__(self, state: dict) -> None:
        if not isinstance(state, dict) or "ticker_symbol" not in state:
            raise DomainValidationError("Stock state must include ticker_symbol.")
        fields = {field: state[field] for field in self._STATE_FIELDS if field in state}
        # Complete candidate validation before replacing any existing state.
        candidate = type(self)(API_KEY=load_configuration().api_key, **fields)
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
