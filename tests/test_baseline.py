"""Regression coverage for the existing watchlist and CLI surfaces."""

import importlib
from pathlib import Path
import socket
import subprocess
import sys
from types import SimpleNamespace
import urllib.request

import pytest
from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parents[1]


def test_all_tracked_python_modules_compile():
    result = subprocess.run(
        ["git", "ls-files", "-z", "*.py"], cwd=ROOT,
        check=True, capture_output=True, text=True,
    )
    for name in filter(None, result.stdout.split("\0")):
        path = ROOT / name
        compile(path.read_bytes(), str(path), "exec")


def test_watchlists_have_independent_stock_lists():
    from watch_list import Watch_list

    first = Watch_list("First")
    second = Watch_list("Second")
    stock = SimpleNamespace(ticker_symbol="AAPL")
    first.add_stock(stock)
    assert first.stocks == [stock]
    assert second.stocks == []
    assert not second.check_stock_existance("AAPL")


def test_add_remove_and_presence():
    from watch_list import Watch_list

    watchlist = Watch_list("Example")
    apple = SimpleNamespace(ticker_symbol="AAPL")
    microsoft = SimpleNamespace(ticker_symbol="MSFT")
    assert not watchlist.check_stock_existance("AAPL")
    watchlist.add_stock(apple)
    watchlist.add_stock(microsoft)
    assert watchlist.check_stock_existance("AAPL")
    assert watchlist.check_stock_existance("MSFT")
    watchlist.remove_stock("AAPL")
    assert not watchlist.check_stock_existance("AAPL")
    assert watchlist.stocks == [microsoft]
    watchlist.remove_stock("MISSING")
    assert watchlist.stocks == [microsoft]


@pytest.mark.parametrize("tickers", [[], ["AAPL", "MSFT"]])
def test_ticker_listing(tickers, capsys):
    from watch_list import Watch_list

    watchlist = Watch_list("Example")
    for ticker in tickers:
        watchlist.add_stock(SimpleNamespace(ticker_symbol=ticker))
    watchlist.show_just_tickers()
    output = capsys.readouterr().out
    assert "All Stocks" in output
    assert "Tickers" in output
    for ticker in tickers:
        assert ticker in output
    for missing in {"AAPL", "MSFT"} - set(tickers):
        assert missing not in output


def test_unfinished_method_is_explicitly_unavailable():
    from watch_list import Watch_list

    with pytest.raises(NotImplementedError, match="not implemented"):
        Watch_list("Example").show_stocks_daniil_method()


@pytest.fixture
def cli_module(request):
    name = request.param
    previous = sys.modules.pop(name, None)
    try:
        yield importlib.import_module(name)
    finally:
        sys.modules.pop(name, None)
        if previous is not None:
            sys.modules[name] = previous


@pytest.mark.parametrize(
    "cli_module", ["menu_watchlist", "daniils_stock_method"], indirect=True,
)
def test_cli_help_without_credentials_or_state(cli_module, tmp_path):
    assert cli_module.API_KEY is None
    assert cli_module.current_watchlist.stocks == []
    result = CliRunner().invoke(cli_module.app, ["--help"], terminal_width=120)
    assert result.exit_code == 0, result.output
    assert "Usage:" in result.output
    for command in ("add-stock", "remove-stock", "show-stocks", "refresh"):
        assert command in result.output
    if cli_module.__name__ == "menu_watchlist":
        assert "graph-stock" in result.output
    assert not (tmp_path / cli_module.WATCHLIST_FILE).exists()
    assert not (tmp_path / "list_of_valid_tickers.csv").exists()


def test_csv_writes_are_isolated(tmp_path):
    from utils import utility_module

    utility_module.write_file("AAPL")
    tickers = []
    utility_module.read_file(tickers)
    assert tickers == [["AAPL"]]
    assert (tmp_path / "list_of_valid_tickers.csv").is_file()


def test_unmocked_network_is_denied():
    with pytest.raises(pytest.fail.Exception, match="Network access denied"):
        urllib.request.urlopen("https://example.invalid/")
    with socket.socket() as transport:
        with pytest.raises(pytest.fail.Exception, match="Network access denied"):
            transport.connect(("127.0.0.1", 443))
    from utils import utility_module

    with pytest.raises(pytest.fail.Exception, match="Network access denied"):
        utility_module.get_jsonparsed_data("https://example.invalid/")
