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
        """
        Adds a stock instance to the watchlist.

        Args:
            stock (Stock): stock object.
        """
        self.stocks.append(stock)
    
    def graph_stock(self, stock_ticker: str):
        """
        Finds a stock instance based on the ticker symbol and if found runs stock class function to display a graph.
        
        Args:
            stock_ticker (str): stock ticker symbol provided by user.
        """
        for stock in self.stocks:
            if stock_ticker == stock.ticker_symbol:
                stock.graph_performance()
                
    def remove_stock(self, stock_ticker: str):
        """
        Finds a stock instance based on the ticker symbol and if found removes that stock from the watchlist.
        
        Args:
            stock_ticker (str): stock ticker symbol provided by user.
        """
        for stock in self.stocks:
            if stock_ticker == stock.ticker_symbol:
                self.stocks.remove(stock)
    
    def check_stock_existance(self, stock_ticker:str):
        """
        Searches for a stock instance based on the ticker symbol. 
        If found return true. If not found returns false.
        
        Args:
            stock_ticker (str): stock ticker symbol provided by user.
        """
        for stock in self.stocks:
            if stock_ticker == stock.ticker_symbol:
                return True
        
        return False
        
    def show_just_tickers(self):
        """
        Creates a table using rich library that shows the tickers of all the stock instances inside the watchlist.
        """
        table = Table(title="All Stocks")
        table.add_column("Tickers")
        
        for stock in self.stocks:
            table.add_row(stock.ticker_symbol)
            
        #creates console and prints table
        console = Console()
        console.print(table)
          
    def show_stocks(self):
        """
        Creates a table using rich library which displays all information about the stocks inside the watchlist.
        For percent return attributes wraps them in green or red color based on their value. 
        """
        #creates the table object
        table = Table(title=f"{self.name}")
        
        #creates columns
        table.add_column("Exchange", style="white", no_wrap=True)
        table.add_column("Ticker", style="white")
        table.add_column("Company name", style="white")
        table.add_column("Market Cap", style="white")
        table.add_column("Amount Owned", style="white")
        table.add_column("Cost Basis", style="white")
        table.add_column("Price", style="white")
        table.add_column("Your Total Return", style="white")
        table.add_column("1D", style="white")
        table.add_column("5D", style="white")
        table.add_column("1M", style="white")
        table.add_column("3M", style="white")
        table.add_column("6M", style="white")
        table.add_column("1Y", style="white")
        table.add_column("3Y", style="white")
        table.add_column("5Y", style="white")
        table.add_column("Sector", style="white")
        table.add_column("Country", style="white")
        
        for stock in self.stocks: #calls stock attributes 
           table.add_row(stock.exchange, stock.ticker_symbol, stock.name, stock.market_cap, stock.amount_owned, stock.cost_basis, stock.current_price, Watch_list.wrap_percent(stock.total_return) , Watch_list.wrap_percent(stock.price_1d), 
                         Watch_list.wrap_percent(stock.price_5d), Watch_list.wrap_percent(stock.price_30d), Watch_list.wrap_percent(stock.price_3m), Watch_list.wrap_percent(stock.price_6m), Watch_list.wrap_percent(stock.price_1y), 
                         Watch_list.wrap_percent(stock.price_3y), Watch_list.wrap_percent(stock.price_5y), stock.sector,  stock.country,) 
        
        #creates console and prints table
        console = Console()
        console.print(table)
    
    def refresh_stocks(self):
        """
        Goes through all stock instances inside this instance and uses stock class functions to updates the attributes inside the stock instances.
        
        Attributes updated:
            Updates all attributes (besides API Key) for all stock instances inside the watchlist.
        """
        for stock in self.stocks:
            stock.get_stock_info()
            stock.get_price_over_time()   
            stock.calculate_return()
    
    def wrap_percent(percent):
        """
        Wraps a percent variable into a specific color based on its float value and adds a percent sign at the end.

        Args:
            percent (str): Percent value in a string format.

        Returns:
            str: A string with colored text and percent sign at the end.
        """
        return f"[{ Watch_list.get_color(float(percent))}]{percent}%[/]"
    
    @staticmethod       
    def get_color(value: float):
        """
        Returns color name based on the value of a variable.

        Args:
            value (float): Numerical value.

        Returns:
            str: Name of a color.
        """
        if value >= 0:
            return "green"
        else:
            return "red"
