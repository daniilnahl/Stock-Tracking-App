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
        
    def remove_stock(self, stock: object):
        self.stocks.remove(stock)
    
    @property
    def get_name(self):
        return self.name
    
    @get_name.setter
    def change_name(self):
        new_name = input('Enter the new name of this watch list: ')  
        self.name = new_name
             
    def show_stocks(self):
        #creates the table object
        table = Table(title=f"{self.name}")
        
        #creates columns
        table.add_column("Exchange", style="magenta", no_wrap=True)
        table.add_column("Ticker", style="magenta")
        table.add_column("Company name", style="magenta")
        table.add_column("Price", style="magenta")
        table.add_column("Market Cap", style="magenta")
        table.add_column("Sector", style="magenta")
        table.add_column("Country", style="magenta")
        
        for stock in self.stocks: #calls stock attributes 
           table.add_row(stock.exchange, stock.ticker_symbol, stock.name, stock.price, stock.market_cap, stock.sector,  stock.country) 
           
        #creates console and prints table
        console = Console()
        console.print(table)
        