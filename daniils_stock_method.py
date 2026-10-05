import os
from config import ConfigurationError, load_configuration, require_api_key

import typer 

#OBJECTS 
from stock import Stock
from stock_tracker.domain import DomainValidationError
from stock_tracker.exceptions import StockTrackerError
from watch_list import Watch_list

#helper functions
from utils import utility_module
import pickle

#gets API_KEY from the virtual environment
API_KEY = load_configuration().api_key

#functions to handle saving watchlist 
def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "wb") as f: #wb - binary write mode
        pickle.dump(watchlist, f)

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "rb") as f: #rb - binary read mode
            return pickle.load(f)
    return Watch_list("Watchlist")

WATCHLIST_FILE = "daniils_stock_methodd.pkl" 
current_watchlist = load_watchlist()#loads it from an external file

app = typer.Typer()

@app.callback()
def validate_configuration(ctx: typer.Context):
    if ctx.invoked_subcommand in {"add-stock", "refresh"}:
        try:
            require_api_key(API_KEY)
        except ConfigurationError as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(code=1) from None

@app.command()
def add_stock():
    stock_ticker = (typer.prompt("Enter stock ticker")).upper()
    try:
        stock_valid = utility_module.check_ticker(stock_ticker, API_KEY)
        if not stock_valid:
            typer.echo("Invalid ticker. Try again.")
            return
        if current_watchlist.check_stock_existance(stock_ticker):
            typer.echo("Stock already exists in the watchlist.")
            return
        stock = Stock(stock_ticker, API_KEY)
        stock.get_stock_info()
        stock.get_price_over_time()
        while True:
            try:
                stock_amount = typer.prompt("Enter amount of stocks owned")
                stock_cb = typer.prompt("Enter average cost per share of owned stocks")
                stock.set_owned_data(stock_amount, stock_cb)
                break
            except DomainValidationError as error:
                typer.echo(f"Invalid input. {error} Please try again.")
    except (StockTrackerError, ConfigurationError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from None
    current_watchlist.add_stock(stock)
    save_watchlist(current_watchlist)
    typer.echo("Succesfully added stock to watchlist.")
 
@app.command()  
def remove_stock():
    current_watchlist.show_just_tickers()
    stock_ticker = (typer.prompt("Enter stock ticker")).upper()
    current_watchlist.remove_stock(stock_ticker)#removes the stock
    current_watchlist.show_just_tickers()
    save_watchlist(current_watchlist)#updates the external file


@app.command()
def show_stocks():
    current_watchlist.show_stocks()

@app.command()
def refresh():
    try:
        current_watchlist.refresh_stocks()
    except (StockTrackerError, ConfigurationError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from None
    typer.echo("Succesfully updated stocks data.")
    save_watchlist(current_watchlist)
