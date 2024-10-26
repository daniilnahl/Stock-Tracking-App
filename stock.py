from dataclasses import dataclass
import requests 

@dataclass
class Stock:
    #needed
    ticker_symbol: str
    API_KEY: str
    #stock price
    open_price: float = None
    close_price: float = None
    low_price: float = None
    high_price: float = None
    #other info
    sector: str = None
    market_cap: float = None
    eps: float = None #earning per share
    pe: float = None #price to earning
    
    #gets basic stock info
    def get_company_overview(self):
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={self.ticker_symbol}&apikey={self.API_KEY}"
        r = requests.get(url)
        data = r.json() #converts json into dictionary
        type(data)#chekcs for type 
        
        #sets all of the values for the stock
        self.sector = data['Sector']
        self.market_cap = data['MarketCapitalization']
        self.eps = data['EPS']
        self.pe = data['PERatio']
        
    #gets daily price info
    
        
    
