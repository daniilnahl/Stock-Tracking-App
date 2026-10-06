from pathlib import Path
from config import ConfigurationError, load_configuration, require_api_key

import typer #CLI

#OBJECTS 
from stock import Stock
from stock_tracker.domain import DomainValidationError
from stock_tracker.exceptions import PersistenceError, StockTrackerError
from stock_tracker.compatibility.cli_persistence import (
    load_cli_watchlist, save_cli_watchlist, storage_error_message,
)
from watch_list import Watch_list

#helper functions
from utils import utility_module

#gets API_KEY from the virtual environment
API_KEY = load_configuration().api_key

# Select cwd-relative storage once per process; importing does not load state.
WATCHLIST_FILE = Path.cwd() / "stock_tracker.sqlite3"
WATCHLIST_NAMESPACE = "menu_watchlist"
LEGACY_WATCHLIST_FILE = Path.cwd() / "watchlist.pkl"
current_watchlist = Watch_list("Watchlist")
_watchlist_loaded = False


def save_watchlist(watchlist):
    """Commit this CLI namespace without persisting runtime credentials."""
    global _watchlist_loaded
    save_cli_watchlist(WATCHLIST_FILE, WATCHLIST_NAMESPACE, LEGACY_WATCHLIST_FILE, watchlist)
    if watchlist is current_watchlist:
        _watchlist_loaded = True


def load_watchlist():
    """Restore local state offline; inspect legacy file existence only."""
    return load_cli_watchlist(WATCHLIST_FILE, WATCHLIST_NAMESPACE, LEGACY_WATCHLIST_FILE, API_KEY)


def _ensure_watchlist_loaded():
    global _watchlist_loaded
    if not _watchlist_loaded:
        restored = load_watchlist()
        # Keep references and explicitly supplied in-memory state for existing callers.
        if not current_watchlist.stocks:
            current_watchlist.name = restored.name
            current_watchlist.stocks[:] = restored.stocks
        _watchlist_loaded = True


def _save_current_watchlist():
    try:
        save_watchlist(current_watchlist)
    except PersistenceError as error:
        typer.echo(storage_error_message(error), err=True)
        raise typer.Exit(code=1) from None

app = typer.Typer()

def _prepare_command(*, network=False):
    """Run preflight only for command execution, after eager help processing."""
    try:
        if network:
            require_api_key(API_KEY)
        _ensure_watchlist_loaded()
    except PersistenceError as error:
        typer.echo(storage_error_message(error), err=True)
        raise typer.Exit(code=1) from None
    except ConfigurationError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from None


@app.callback()
def validate_configuration(ctx: typer.Context):
    """Select a command; help never loads state or requires credentials."""

@app.command()
def add_stock():
    """add a stock to the watchlist."""
    _prepare_command(network=True)
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
    _save_current_watchlist()
    typer.echo("Succesfully added stock to watchlist.")
 
@app.command()  
def remove_stock():
    """
    remove a stock from the watchlist.
    """
    _prepare_command()
    current_watchlist.show_just_tickers()
    stock_ticker = (typer.prompt("Enter stock ticker")).upper()
    current_watchlist.remove_stock(stock_ticker)#removes the stock
    current_watchlist.show_just_tickers()
    _save_current_watchlist()#updates the external file

@app.command()
def graph_stock():
    """
    shows an approximate graph of a stock's performance.
    """
    _prepare_command()
    current_watchlist.show_just_tickers()
    stock_ticker = (typer.prompt("Enter stock ticker")).upper()
    current_watchlist.graph_stock(stock_ticker)
    
@app.command()
def show_stocks():
    """
    display a comprehensive table of the stocks, including relevant financial data.
    """
    _prepare_command()
    current_watchlist.show_stocks()

@app.command()
def refresh():
    """update stocks data to ensure accuracy and reflect the most current market information."""
    _prepare_command(network=True)
    try:
        current_watchlist.refresh_stocks()
    except (StockTrackerError, ConfigurationError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from None
    _save_current_watchlist()
    typer.echo("Succesfully updated stocks data.")

       
if __name__ == "__main__":
    app()
