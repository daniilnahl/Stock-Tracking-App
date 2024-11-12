#CLASS FOR A STOCK 
from dataclasses import dataclass
from urllib.request import urlopen
import json
import certifi
import utils.tickers_file_module as tfm

@dataclass
class Stock:
    #required
    ticker_symbol: str
    API_KEY: str
    
    #text info
    name: str = None
    sector: str = None
    country: str = None
    exchange: str = None
    
    #numerical info
    price: str = None
    market_cap: str = None
    
    #misc info
    currency: str = None
    
    @staticmethod
    def get_jsonparsed_data(url):
        response = urlopen(url, cafile=certifi.where())
        data = response.read().decode("utf-8")
        return json.loads(data)
    
    def get_stock_info(self):
        """Assigns data to an instance of a stock class"""
        url = (f"https://financialmodelingprep.com/api/v3/profile/{self.ticker_symbol}?apikey={self.API_KEY}")
        data = Stock.get_jsonparsed_data(url)
       
        #gets numerical data
        self.market_cap = Stock.format_mcap(data[0]['mktCap'])
        self.price = str(data[0]['price'])
        
        #text info
        self.name = data[0]['companyName']
        self.sector = data[0]['sector']
        self.country = data[0]['country']
        self.exchange = data[0]['exchange']
        
        #misc info
        self.currency = data[0]['currency']
        
    def check_ticker(self):
        valid_tickers_list = []
        tfm.read_file(valid_tickers_list)
        
        #checks if the ticker symbol is found on file(valid_tickers_list)
        found_ticker = any(self.ticker_symbol == valid_ticker[0] for valid_ticker in valid_tickers_list)
        
        #if ticker found return true
        if found_ticker:
            return True
        else: #checks if provided ticker is valid using API
            url = (f"https://financialmodelingprep.com/api/v3/search-ticker?query={self.ticker_symbol}&limit=10&exchange=NASDAQ&apikey={self.API_KEY}")
            data = Stock.get_jsonparsed_data(url)

            # Check the API response
            if data == []:  #empty list means ticker wasn't found
                return False
            else:
                tfm.write_file(self.ticker_symbol)
                return True    
                
    @staticmethod               
    def format_mcap(mcap: float):    
        if abs(mcap) >= 1_000_000_000_000:
            return f"{mcap / 1_000_000_000_000:.2f}T" #trillions
        else:
            return f"{mcap / 1_000_000_000:.3f}B"  #billions
        
    def get_realtime_price(self): #gets real time price of the stock
        url = (f"https://financialmodelingprep.com/api/v3/quote-short/{self.ticker_symbol}?apikey={self.API_KEY}")
        data = Stock.get_jsonparsed_data(url)
        
        self.price = str(data[0]['price']) 
    
    #def get price change over time in numbers. NOT PERCENT. https://financialmodelingprep.com/api/v3/stock-price-change/AAPL
   
   
    
# when you will get to updating already created watch list when user launches the app there is a bulk API request which lets you get data for multiple stocks through one requests:Multiple Company Prices API
# Get multiple company prices at once
# https://financialmodelingprep.com/api/v3/quote/AAPL,MSFT