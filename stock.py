from dataclasses import dataclass
from urllib.request import urlopen
import json
import certifi
import tickers_file_module as tfm

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
    price: float = None
    market_cap: float = None
    
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
        self.market_cap = data[0]['mktCap']
        self.price = data[0]['price']
        
        #text info
        self.name = data[0]['companyName']
        self.sector = data[0]['sector']
        self.country = data[0]['country']
        self.exchange = data[0]['exchange']
        
        #misc info
        self.currency = data[0]['currency']
        
    def check_ticker(self):
        valid_tickers_list = []
        tfm.read_file(valid_tickers_list)#store valid tickers into a list variable
        print(valid_tickers_list)
        
        if self.ticker_symbol not in valid_tickers_list:
            print('ticker not on file')
            
            #uses api search to see if the ticker exists 
            url = (f"https://financialmodelingprep.com/api/v3/search-ticker?query={self.ticker_symbol}&limit=10&exchange=NASDAQ&apikey={self.API_KEY}")
            data = Stock.get_jsonparsed_data(url)
            
            print(data)
            
            if data == [ ]:#returns [ ] list if cant find a ticker
                print('data is empty')
                return False
            else:#ONLY RECORDS THE LAST TICKER THAT WAS CALLED FIx THIS
                tfm.write_file(self.ticker_symbol)
                return True
        #if ticker exists on local file then its valid        
        else:
            return True
            
        