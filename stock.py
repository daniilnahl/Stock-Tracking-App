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
        tfm.read_file(valid_tickers_list)
        print(valid_tickers_list)
        
        # Check if valid_tickers_list has been populated correctly
        if not valid_tickers_list:
            print("No valid tickers found in file. Exiting the search loop.")
        else:
            # Loop through the list to search for the ticker symbol
            for valid_ticker in valid_tickers_list:
                if self.ticker_symbol == valid_ticker[0]: #checks if ticker matches
                    print("Found ticker on file.")
                    break  # Exit the loop since we found the ticker

            #If ticker was not found in the list perform API search
            else:  
                print("Ticker not found on file. Searching via API...")
                #API call
                url = (f"https://financialmodelingprep.com/api/v3/search-ticker?query={self.ticker_symbol}&limit=10&exchange=NASDAQ&apikey={self.API_KEY}")
                data = Stock.get_jsonparsed_data(url)

                # Check the API response
                if data == []:  #empty list means ticker wasn't found
                    print("Ticker not found via API.")
                else:
                    tfm.write_file(self.ticker_symbol)
                    print("Found ticker via API. Recording ticker to file.")
            
        