from pathlib import Path
from datetime import date
from config import ConfigurationError, load_configuration, require_api_key

import typer #CLI

#OBJECTS 
from stock import Stock as Stock
from stock_tracker.domain import DomainValidationError
from stock_tracker.exceptions import HistoryRangeError, PersistenceError, StockTrackerError
from stock_tracker.compatibility.history_operations import require_history_identity
from stock_tracker.compatibility.watchlist_persistence import watchlist_to_record
from stock_tracker.cli.composition import (
    append_prepared, current_service, history_service, local_service, refresh_watchlist, remove_from_watchlist,
)
from stock_tracker.cli.presentation import project_prepared, render_history, render_watchlist
from stock_tracker.compatibility.cli_persistence import (
    load_cli_watchlist, save_cli_watchlist, storage_error_message,
)
from watch_list import Watch_list

#helper functions
from utils import utility_module as utility_module

#gets API_KEY from the virtual environment
API_KEY = load_configuration().api_key

# Select cwd-relative storage once per process; importing does not load state.
WATCHLIST_FILE = Path.cwd() / "stock_tracker.sqlite3"
HISTORY_CACHE_FILE = Path.cwd() / "stock_tracker.history-cache.json"
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
        service = current_service(current_watchlist, API_KEY)
        record = watchlist_to_record(current_watchlist, WATCHLIST_NAMESPACE)
        prepared = service.prepare_add(record, stock_ticker)
        if prepared.status == "invalid":
            typer.echo("Invalid ticker. Try again.")
            return
        if prepared.status == "duplicate":
            typer.echo("Stock already exists in the watchlist.")
            return
        while True:
            try:
                stock_amount = typer.prompt("Enter amount of stocks owned")
                stock_cb = typer.prompt("Enter average cost per share of owned stocks")
                ownership = service.validate_ownership(stock_amount, stock_cb)
                break
            except DomainValidationError as error:
                typer.echo(f"Invalid input. {error} Please try again.")
        candidate = project_prepared(service.finish_add(record, prepared, ownership))
    except (StockTrackerError, ConfigurationError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from None
    append_prepared(current_watchlist, candidate, API_KEY)
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
    remove_from_watchlist(local_service(WATCHLIST_FILE, WATCHLIST_NAMESPACE, LEGACY_WATCHLIST_FILE),
                          current_watchlist, WATCHLIST_NAMESPACE, stock_ticker)
    current_watchlist.show_just_tickers()
    _save_current_watchlist()#updates the external file

@app.command()
def graph_stock(
    start: str | None = typer.Option(None, help="Inclusive start date (YYYY-MM-DD); requires --end."),
    end: str | None = typer.Option(None, help="Inclusive end date (YYYY-MM-DD); requires --start."),
):
    """Show genuine raw historical closes for a selected watchlist stock."""
    try:
        explicit = start is not None or end is not None
        if explicit:
            try:
                first, last = date.fromisoformat(start), date.fromisoformat(end)
                if first.isoformat() != start or last.isoformat() != end:
                    raise HistoryRangeError()
            except (TypeError, ValueError):
                raise HistoryRangeError() from None
            first, last = history_service(current_watchlist, HISTORY_CACHE_FILE).validate_range(first, last)
        _prepare_command()
        current_watchlist.show_just_tickers()
        stock_ticker = (typer.prompt("Enter stock ticker")).upper()
        selected = [(ordinal, stock) for ordinal, stock in enumerate(current_watchlist.stocks)
                    if stock.ticker_symbol == stock_ticker]
        if not selected:
            return
        for _, stock in selected:
            require_history_identity(stock)
        require_api_key(API_KEY)
        previous_keys = [(stock, stock.API_KEY) for _, stock in selected]
        try:
            for stock, _ in previous_keys:
                stock.API_KEY = API_KEY
            record = watchlist_to_record(current_watchlist, WATCHLIST_NAMESPACE)
            service = history_service(current_watchlist, HISTORY_CACHE_FILE)
            for ordinal, _ in selected:
                options = {"start": first, "end": last} if explicit else {}
                render_history(service.history(record.entries[ordinal].stock, ordinal=ordinal, **options))
        finally:
            for stock, key in previous_keys:
                stock.API_KEY = key
    except ConfigurationError:
        typer.echo("Unable to configure historical market data. Check FMP_API_KEY.", err=True)
        raise typer.Exit(code=1) from None
    except StockTrackerError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from None
    
@app.command()
def show_stocks():
    """
    display a comprehensive table of the stocks, including relevant financial data.
    """
    _prepare_command()
    service = local_service(WATCHLIST_FILE, WATCHLIST_NAMESPACE, LEGACY_WATCHLIST_FILE)
    render_watchlist(service.view(watchlist_to_record(current_watchlist, WATCHLIST_NAMESPACE)))

@app.command()
def refresh():
    """update stocks data to ensure accuracy and reflect the most current market information."""
    _prepare_command(network=True)
    try:
        refresh_watchlist(current_watchlist, WATCHLIST_NAMESPACE, current_service(current_watchlist, API_KEY))
    except (StockTrackerError, ConfigurationError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from None
    _save_current_watchlist()
    typer.echo("Succesfully updated stocks data.")

       
if __name__ == "__main__":
    app()
