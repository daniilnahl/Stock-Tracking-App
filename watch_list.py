#CLASS FOR A WATCH LIST
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table

@dataclass
class Watch_list:
    name: str
    #use default_factory to intialize an empty list for each instance because without the list would used across all the class instances(big no no. Also without it you get a value error).
    stocks: list = field(default_factory=list)
    
    def add_stock(self, stock: object):
        self.stocks.append(stock)
        
    def remove_stock(self, stock_ticker: str):
        for stock in self.stocks:
            if stock_ticker == stock.ticker_symbol:
                self.stocks.remove(stock)
    
    def check_stock_existance(self, stock_ticker:str):
        for stock in self.stocks:
            if stock_ticker == stock.ticker_symbol:
                return True
        
        return False
    
    def change_name(self, new_name=""):
        new_name = input('Enter  new name for this watch list: ')  
        self.name = new_name
    
    def show_just_tickers(self):
        table = Table(title="All Stocks")
        table.add_column("Tickers")
        
        for stock in self.stocks:
            table.add_row(stock.ticker_symbol)
            
        #creates console and prints table
        console = Console()
        console.print(table)
          
    def show_stocks(self):
        #creates the table object
        table = Table(title=f"{self.name}")
        
        #creates columns
        table.add_column("Exchange", style="magenta", no_wrap=True)
        table.add_column("Ticker", style="magenta")
        table.add_column("Company name", style="magenta")
        table.add_column("Market Cap", style="magenta")
        table.add_column("Amount Owned", style="magenta")
        table.add_column("Cost Basis", style="magenta")
        table.add_column("Price", style="magenta")
        table.add_column("Your Total Return", style="magenta")
        table.add_column("1D", style="magenta")
        table.add_column("5D", style="magenta")
        table.add_column("1M", style="magenta")
        table.add_column("3M", style="magenta")
        table.add_column("6M", style="magenta")
        table.add_column("1Y", style="magenta")
        table.add_column("3Y", style="magenta")
        table.add_column("5Y", style="magenta")
        table.add_column("Sector", style="magenta")
        table.add_column("Country", style="magenta")
        
        for stock in self.stocks: #calls stock attributes 
           table.add_row(stock.exchange, stock.ticker_symbol, stock.name, stock.market_cap, stock.amount_owned, stock.cost_basis, stock.current_price, stock.total_return, stock.price_1d, stock.price_5d, 
                         stock.price_30d, stock.price_3m, stock.price_6m, stock.price_1y,stock.price_3y, stock.price_5y, stock.sector,  stock.country,) 
        
        #creates console and prints table
        console = Console()
        console.print(table)
    
    def refresh_stocks(self):
        for stock in self.stocks:
            stock.get_stock_info()
            stock.get_price_over_time()   