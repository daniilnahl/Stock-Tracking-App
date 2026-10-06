"""Source/wheel processes execute both CLI namespaces without pickle/network IO."""

from contextlib import ExitStack
from decimal import Decimal
import importlib
import os
from pathlib import Path
import pickle
import socket
import sys
import urllib.request
from unittest.mock import patch


def denied(*args, **kwargs):
    raise AssertionError("Network/pickle/provider access denied")


def main():
    root, source, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    sys.path[:0] = [str(root), str(source)]
    os.environ.pop("MY_API_KEY", None)
    os.environ.pop("FMP_API_KEY", None)
    os.environ["MPLBACKEND"] = "Agg"
    os.environ["MPLCONFIGDIR"] = str(Path.cwd() / "matplotlib")
    os.environ["COLUMNS"] = "300"
    if mode == "write":
        os.environ["FMP_API_KEY"] = "synthetic-cli-probe-runtime"
    with ExitStack() as guards:
        for target, attribute in (
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        import dotenv
        guards.enter_context(patch.object(dotenv, "load_dotenv", lambda *a, **k: False))
        from stock import Stock
        from stock_tracker.providers import factory
        guards.enter_context(patch.object(factory, "create_market_data_provider", denied))
        from typer.testing import CliRunner
        from stock_tracker.domain import Portfolio
        from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
        modules = [importlib.import_module(name) for name in ("menu_watchlist", "daniils_stock_method")]
        database = Path.cwd() / "stock_tracker.sqlite3"
        for index, module in enumerate(modules):
            assert module.current_watchlist.stocks == []
            with patch.object(module, "load_watchlist", denied):
                commands = ["show-stocks", "add-stock", "remove-stock", "refresh"]
                if index == 0:
                    commands.append("graph-stock")
                for args in [["--help"], *[[command, "--help"] for command in commands]]:
                    result = CliRunner().invoke(module.app, args)
                    assert result.exit_code == 0, result.output
            if mode == "write":
                with patch.object(module.utility_module, "check_ticker", lambda *a: True), \
                        patch.object(Stock, "get_stock_info", lambda stock: (
                            setattr(stock, "name", "Fictional"), setattr(stock, "exchange", "NASDAQ"),
                            setattr(stock, "current_price", "120"))), \
                        patch.object(Stock, "get_price_over_time", lambda stock: None):
                    result = CliRunner().invoke(module.app, ["add-stock"],
                                               input="aapl\n0.12345678901234567890123456789\n100\n")
                    assert result.exit_code == 0 and "Succesfully added" in result.output
                first = module.current_watchlist.stocks[0]
                module.current_watchlist.name = "Menu" if index == 0 else "Method"
                module.current_watchlist.stocks.append(first)
                module.current_watchlist.stocks.append(Stock("UNOWNED", None, current_price=None))
                module.save_watchlist(module.current_watchlist)
                module.LEGACY_WATCHLIST_FILE.write_bytes(b"untouched untrusted legacy bytes")
            else:
                assert mode == "read"
                before = database.read_bytes()
                result = CliRunner().invoke(module.app, ["show-stocks"], terminal_width=300)
                assert result.exit_code == 0 and "AAPL" in result.output
                saved = module.current_watchlist
                assert saved.name == ("Menu" if index == 0 else "Method")
                assert [stock.ticker_symbol for stock in saved.stocks] == ["AAPL", "AAPL", "UNOWNED"]
                assert saved.stocks[0]._position.quantity == Decimal("0.12345678901234567890123456789")
                assert saved.stocks[0]._position.average_cost == Decimal("100")
                assert saved.stocks[0].API_KEY is None and saved.stocks[1].API_KEY is None
                assert saved.stocks[2]._position is None and saved.stocks[2].current_price is None
                assert database.read_bytes() == before
                assert module.LEGACY_WATCHLIST_FILE.read_bytes() == b"untouched untrusted legacy bytes"
            assert Path(module.__file__).resolve().is_relative_to(root.resolve())
        repository = SQLitePortfolioRepository(database)
        if mode == "write":
            repository.create(Portfolio(7, "Portfolio"))
        else:
            assert repository.get(7).name == "Portfolio"
        assert b"synthetic-cli-probe-runtime" not in database.read_bytes()


if __name__ == "__main__":
    main()
