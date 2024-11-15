from dataclasses import dataclass
import utils.utility_module as um

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
    
    def get_stock_info(self):
        """Assigns data to an instance of a stock class"""
        url = (f"https://financialmodelingprep.com/api/v3/profile/{self.ticker_symbol}?apikey={self.API_KEY}")
        data = um.get_jsonparsed_data(url)

        if data == [] or data is None: #handles a situation when API request encounter an error and return empty data or []
            print("API request failed. Please try again.")
            self.price ='N/A'
            self.market_cap ='N/A'
            self.name ='N/A'
            self.sector = 'N/A'
            self.country ='N/A'
            self.exchange ='N/A'
            self.currency ='N/A'
            return None
        
        else:
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
        
    def get_realtime_price(self): #gets real time price of the stock
        url = (f"https://financialmodelingprep.com/api/v3/quote-short/{self.ticker_symbol}?apikey={self.API_KEY}")
        data = um.get_jsonparsed_data(url)
        
        if data == [] or data is None: #handles a situation when API request encounter an error and return empty data or []
            print("API request failed. Please try again.")
            self.price = 'N/A'
            return None
        
        else:
            self.price = str(data[0]['price']) 
            
    @staticmethod               
    def format_mcap(mcap: float):    
        if abs(mcap) >= 1_000_000_000_000:
            return f"{mcap / 1_000_000_000_000:.2f}T" #trillions
        else:
            return f"{mcap / 1_000_000_000:.3f}B"  #billions
            
    #def get price change over time in numbers. NOT PERCENT. https://financialmodelingprep.com/api/v3/stock-price-change/AAPL
   
   
    
# when you will get to updating already created watch list when user launches the app there is a bulk API request which lets you get data for multiple stocks through one requests:Multiple Company Prices API
# Get multiple company prices at once
# https://financialmodelingprep.com/api/v3/quote/AAPL,MSFT