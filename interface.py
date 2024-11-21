import main #api key
import typer #CLI

#OBJECTS 
from stock import Stock
from watch_list import Watch_list

#helper functions
from utils import utility_module
import pickle
import os

#functions to handle saving watchlist 
def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "wb") as f:
        pickle.dump(watchlist, f)

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "rb") as f:
            return pickle.load(f)
    return Watch_list("Watchlist")

WATCHLIST_FILE = "watchlist.pkl" 
current_watchlist = load_watchlist()#loads it from an external file

app = typer.Typer()

@app.command()
def add_stock():
    stock_ticker = (typer.prompt("Enter stock ticker")).upper()
    stock_valid = utility_module.check_ticker(stock_ticker, main.API_KEY)
    
    if stock_valid == False: #if stock ticker is invalid
        typer.echo("Invalid ticker. Try again.")
    else:#if stock ticker is valid we create an instance of the object and fill it up with data
        stock = Stock(stock_ticker, main.API_KEY)   
        stock.get_stock_info()
        stock.get_price_over_time()
        #record the stock instance into the watchlist
        current_watchlist.add_stock(stock)
        save_watchlist(current_watchlist)#updates the external file
 
@app.command()  
def delete_stock():
    current_watchlist.show_just_tickers()
    stock_ticker = (typer.prompt("Enter stock ticker")).upper()
    current_watchlist.remove_stock(stock_ticker)#removes the stock
    current_watchlist.show_just_tickers()
    save_watchlist(current_watchlist)#updates the external file

@app.command()
def show_stocks():
    current_watchlist.show_stocks()
    

if __name__ == "__main__":
    app()