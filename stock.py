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
    current_price: str = None
    market_cap: str = None
    
    #price over time
    price_1d: str = None
    price_5d: str = None
    price_30d: str = None
    price_3m: str = None
    price_6m: str = None
    price_1y: str = None
    price_5y: str = None
    
    #misc info
    currency: str = None
    
    #user info
    amount_owned: str = None
    price_at_purchase: str = None
           
    def set_owned_amount(self, amount_owned: float, price_at_purchase: float): #setter can only take in one argument
        """
        Sets the amount of stocks owned at a specific price.
        Args:
        amount_owned (float): amount of stocks owned
        price_at_purchase (float): price at which the stocks got owned at 
        """
        self.amount_owned = str(amount_owned)
        self.price_at_purchase = str(price_at_purchase)
        
        
        
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
     
    def get_price_over_time(self):
        url = (f"https://financialmodelingprep.com/api/v3/stock-price-change/{self.ticker_symbol}?apikey={self.API_KEY}")
        data = um.get_jsonparsed_data(url)
        #assigns data
        self.price_1d  =  str(round(data[0]['1D'], 2)) + "%"
        self.price_5d  =  str(round(data[0]['5D'], 2)) + "%"
        self.price_30d =  str(round(data[0]['1M'], 2)) + "%"
        self.price_3m  =  str(round(data[0]['3M'], 2)) + "%"
        self.price_6m  =  str(round(data[0]['6M'], 2)) + "%"
        self.price_1y  =  str(round(data[0]['1Y'], 2)) + "%"
        self.price_5y  =  str(round(data[0]['5Y'], 2)) + "%"
        
    @staticmethod               
    def format_mcap(mcap: float):    
        if abs(mcap) >= 1_000_000_000_000:
            return f"{mcap / 1_000_000_000_000:.2f}T" #trillions
        else:
            return f"{mcap / 1_000_000_000:.3f}B"  #billions