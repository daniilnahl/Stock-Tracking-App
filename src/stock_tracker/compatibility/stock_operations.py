"""Existing FMP orchestration, pending the M2 provider contract."""

from config import require_api_key
from utils import utility_module as um
from . import presentation


def get_stock_info(self):
    """
        Fetches stock profile data from an API and updates the instance's attributes.

        The method sends a GET request to the Financial Modeling Prep API using the stock's ticker symbol
        and assigns the retrieved data (e.g., company name, market cap, current price) to the relevant
        attributes of the stock instance.

        If the API request fails or returns invalid data, the attributes are set to default values (e.g., 'N/A').

        Attributes updated:
        - current_price: The current stock price.
        - market_cap: The company's market capitalization.
        - name: The company's name.
        - sector: The sector the company operates in.
        - country: The company's country of operation.
        - exchange: The stock exchange where the company is listed.
        - currency: The currency used for stock trading.

        Raises:
        - This method does not raise exceptions directly but logs errors if the API request fails.
        """
    url = f'https://financialmodelingprep.com/api/v3/profile/{self.ticker_symbol}?apikey={require_api_key(self.API_KEY)}'
    data = um.get_jsonparsed_data(url)
    if data == [] or data is None:
        print('API request failed. Please try again.')
        self.current_price = 'N/A'
        self.market_cap = 'N/A'
        self.name = 'N/A'
        self.sector = 'N/A'
        self.country = 'N/A'
        self.exchange = 'N/A'
        self.currency = 'N/A'
    else:
        self.market_cap = presentation.format_mcap(data[0]['mktCap'])
        self.current_price = data[0]['price']
        self.name = data[0]['companyName']
        self.sector = data[0]['sector']
        self.country = data[0]['country']
        self.exchange = data[0]['exchange']
        self.currency = data[0]['currency']


def get_realtime_price(self):
    """
        Fetches stock realtime price from an API and updates the instance's attribute.

        The method sends a GET request to the Financial Modeling Prep API using the stock's ticker symbol
        and assigns the retrieved data (current price).

        If the API request fails or returns invalid data, the attribute is set to default value (e.g., 'N/A').

        Attributes updated:
        - current_price: The current stock price.

        Raises:
        - This method does not raise exceptions directly but logs errors if the API request fails.
        """
    url = f'https://financialmodelingprep.com/api/v3/quote-short/{self.ticker_symbol}?apikey={require_api_key(self.API_KEY)}'
    data = um.get_jsonparsed_data(url)
    if data == [] or data is None:
        print('API request failed. Please try again.')
        self.current_price = 'N/A'
    else:
        self.current_price = data[0]['price']


def get_price_over_time(self):
    """
        Fetches stock return data from an API and updates the instance's attributes.

        The method sends a GET request to the Financial Modeling Prep API using the stock's ticker symbol
        and assigns the retrieved data (percent return for last 1 day, 5 days, 1 mounth, etc) to the relevant
        attributes of the stock instance.

        Attributes updated:
        - price_1d: The current stock's percent return for the past 1 day.
        - price_5d: The current stock's percent return for the past 5 days.
        - price_30d: The current stock's percent return for the past 30 days.
        - price_3m: The current stock's percent return for the past 3 months.
        - price_6m: The current stock's percent return for the past 6 months.
        - price_1y: The current stock's percent return for the past 1 year.
        - price_3y: The current stock's percent return for the past 3 years.
        - price_5y: The current stock's percent return for the past 5 years.
        """
    url = f'https://financialmodelingprep.com/api/v3/stock-price-change/{self.ticker_symbol}?apikey={require_api_key(self.API_KEY)}'
    data = um.get_jsonparsed_data(url)
    self.price_1d = str(round(data[0]['1D'], 2))
    self.price_5d = str(round(data[0]['5D'], 2))
    self.price_30d = str(round(data[0]['1M'], 2))
    self.price_3m = str(round(data[0]['3M'], 2))
    self.price_6m = str(round(data[0]['6M'], 2))
    self.price_1y = str(round(data[0]['1Y'], 2))
    self.price_3y = str(round(data[0]['3Y'], 2))
    self.price_5y = str(round(data[0]['5Y'], 2))
