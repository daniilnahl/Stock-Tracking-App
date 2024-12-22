import os
from dotenv import load_dotenv
#gets API_KEY from the virtual environment
load_dotenv()
API_KEY = os.getenv("MY_API_KEY")

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
    """
    Saves the given watchlist to a file.

    This function serializes the watchlist object and writes it to an external file
    using the pickle module. The file is opened in binary write mode.

    Args:
        watchlist (Watch_list): The watchlist object to be saved.
    """
    with open(WATCHLIST_FILE, "wb") as f: #wb - binary write mode
        pickle.dump(watchlist, f)

def load_watchlist():
    """
    Loads the watchlist from a file.

    This function checks if the watchlist file exists. If the file exists, it 
    deserializes and returns the stored watchlist. If the file does not exist,
    it returns a new instance of the Watch_list class.

    Returns:
        Watch_list: The loaded watchlist object or a new Watch_list instance if the file is not found.
    """
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "rb") as f: #rb - binary read mode
            return pickle.load(f)
    return Watch_list("Watchlist")

WATCHLIST_FILE = "watchlist.pkl" 
current_watchlist = load_watchlist()#loads it from an external file

app = typer.Typer()

@app.command()
def add_stock():
    """
    add a stock to the watchlist.
    """
    stock_ticker = (typer.prompt("Enter stock ticker")).upper()
    stock_valid = utility_module.check_ticker(stock_ticker, API_KEY)
    
    if stock_valid == False: #if stock ticker is invalid
        typer.echo("Invalid ticker. Try again.")
    else:#if stock ticker is valid pass
        
        #check if this stock already exists if not create an instance of the object and fill it up with data
        if current_watchlist.check_stock_existance(stock_ticker):
            typer.echo("Stock already exists in the watchlist.")
        
        else:
            stock = Stock(stock_ticker, API_KEY)   
            #gets stock info
            stock.get_stock_info()
            if stock.name == "N/A":
                typer.echo("Warning: API request didn't retrieve any data. Make sure API key was correctly stored and run this command again.")
            else:
                stock.get_price_over_time()
                
                #loop to get user info on owned stocks
                while True:
                    try:
                        stock_amount = typer.prompt("Enter amount of stocks owned", type=(float))
                        stock_cb = typer.prompt("Enter cost basis of owned stocks", type=(float))

                        if stock_amount < 0 or stock_cb < 0: #if values are negative dont add them
                            typer.echo('Invalid input. Please enter numeric values that are greater or equal to 0.')
                        else:
                            stock.set_owned_data(stock_amount, stock_cb)
                            break   
                    except ValueError:
                        typer.echo("Invalid input. Please enter numeric values, such as 10.1 or 123.")
                    
                        
                #record the stock instance into the watchlist
                current_watchlist.add_stock(stock) 
                
                save_watchlist(current_watchlist)#updates the external file
                
                typer.echo("Succesfully added stock to watchlist.")
 
@app.command()  
def remove_stock():
    """
    remove a stock from the watchlist.
    """
    current_watchlist.show_just_tickers()
    stock_ticker = (typer.prompt("Enter stock ticker")).upper()
    current_watchlist.remove_stock(stock_ticker)#removes the stock
    current_watchlist.show_just_tickers()
    save_watchlist(current_watchlist)#updates the external file

@app.command()
def graph_stock():
    """
    shows an approximate graph of a stock's performance.
    """
    current_watchlist.show_just_tickers()
    stock_ticker = (typer.prompt("Enter stock ticker")).upper()
    current_watchlist.graph_stock(stock_ticker)
    
@app.command()
def show_stocks():
    """
    display a comprehensive table of the stocks, including relevant financial data.
    """
    current_watchlist.show_stocks()

@app.command()
def refresh():
    """
    update stocks data to ensure accuracy and reflect the most current market information.
    """
    current_watchlist.refresh_stocks()
    typer.echo("Succesfully updated stocks data.")
    save_watchlist(current_watchlist)
       
if __name__ == "__main__":
    app()