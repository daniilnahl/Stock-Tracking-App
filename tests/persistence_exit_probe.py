"""Independent combined M3 import/backup/restore/restart audit, source or wheel."""

from contextlib import ExitStack
from decimal import Decimal
import importlib
import json
import os
from pathlib import Path
import pickle
import socket
import sys
import urllib.request
from unittest.mock import patch


def denied(*args, **kwargs):
    raise AssertionError("M3 audit denied network/pickle/provider/legacy data IO")


def payload():
    identity = {"symbol": "AAPL", "name": "Exact company", "exchange": "NASDAQ"}
    position = {"stock": identity, "quantity": "0.2500",
                "average_cost": "100.123456789012345678901234567890"}
    unknown = {"stock": {"symbol": "AAPL", "name": None, "exchange": None},
               "quantity": "0E-30", "average_cost": "-0.00"}
    known = {"stock": identity, "quantity": "10", "average_cost": "100"}
    distinct = dict(position, stock=dict(identity, name="Alternate company", exchange="NYSE"),
                    quantity="1E-8", average_cost="100.0000")
    entry = {"stock": identity, "quantity": "0.2500", "average_cost": position["average_cost"],
             "current_price": "0.00", "sector": "Tech", "country": "US", "currency": "USD",
             "market_cap": "1.234B", "price_1d": "", "price_5d": "No observation", "price_30d": "-",
             "price_3m": None, "price_6m": "0", "price_1y": "1.50", "price_3y": "-2",
             "price_5y": "3.125"}
    unowned = dict(entry, stock=unknown["stock"], quantity="0E-30", average_cost=None,
                   current_price=None)
    zero_owned = dict(entry, quantity="0.0000", average_cost="0.00", current_price="0.00")
    other_exchange = dict(entry, stock=distinct["stock"], quantity="1E-8", average_cost="100.0000")
    return {"format": "stock-tracker-neutral", "version": 1,
            "portfolios": [{"id": "10", "name": "Exact Portfolio",
                             "positions": [position, position, unknown, known, distinct]}],
            "watchlists": [{"namespace": namespace, "name": name,
                            "entries": [entry, entry, unowned, zero_owned, other_exchange]}
                           for namespace, name in (("menu_watchlist", "Menu retained"),
                                                   ("daniils_stock_method", "Method retained"))]}


def verify(database):
    from stock_tracker.domain import position_snapshot
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from typer.testing import CliRunner
    portfolio = SQLitePortfolioRepository(database).get(10)
    assert portfolio.name == "Exact Portfolio" and len(portfolio.positions) == 5
    assert portfolio.positions[0].stock == portfolio.positions[1].stock
    assert portfolio.positions[2].stock.exchange is None
    assert str(portfolio.positions[0].quantity) == "0.2500"
    assert str(portfolio.positions[0].average_cost) == "100.123456789012345678901234567890"
    assert str(portfolio.positions[2].quantity) == "0E-30"
    assert str(portfolio.positions[2].average_cost) == "-0.00"
    assert portfolio.positions[4].stock.exchange == "NYSE"
    assert portfolio.positions[4].stock != portfolio.positions[0].stock
    assert str(portfolio.positions[4].quantity) == "1E-8"
    assert str(portfolio.positions[4].average_cost) == "100.0000"
    snapshot = position_snapshot(portfolio.positions[3], Decimal("120"))
    assert (snapshot.cost_basis, snapshot.market_value, snapshot.unrealized_pnl,
            snapshot.unrealized_return) == (Decimal("1000"), Decimal("1200"), Decimal("200"), Decimal("0.20"))
    records = SQLiteWatchlistRepository(database).list()
    assert len(records) == 2
    original = database.read_bytes()
    for expected in payload()["watchlists"]:
        record = next(record for record in records if record.namespace == expected["namespace"])
        assert record.name == expected["name"] and len(record.entries) == 5
        for item, fixture in zip(record.entries, expected["entries"]):
            assert (item.stock.symbol, item.stock.name, item.stock.exchange) == tuple(
                fixture["stock"][field] for field in ("symbol", "name", "exchange"))
            for field in ("quantity", "average_cost", "current_price"):
                actual = getattr(item, field)
                assert (None if actual is None else str(actual)) == fixture[field]
            for field in set(fixture) - {"stock", "quantity", "average_cost", "current_price"}:
                assert getattr(item, field) == fixture[field]
        module = importlib.import_module(expected["namespace"])
        assert module.API_KEY is None and module.current_watchlist.stocks == []
        with patch.object(module, "load_watchlist", denied):
            assert CliRunner().invoke(module.app, ["--help"]).exit_code == 0
            assert CliRunner().invoke(module.app, ["show-stocks", "--help"]).exit_code == 0
        result = CliRunner().invoke(module.app, ["show-stocks"], terminal_width=300)
        assert result.exit_code == 0 and "AAPL" in result.output, (result.output, repr(result.exception))
        assert module.current_watchlist.name == expected["name"]
        stocks = module.current_watchlist.stocks
        assert len(stocks) == 5 and all(stock.API_KEY is None for stock in stocks)
        assert stocks[0]._position.quantity == Decimal("0.2500")
        assert str(stocks[0]._position.average_cost) == "100.123456789012345678901234567890"
        assert stocks[0].current_price == "0.00" and stocks[0].total_return == "-100.0"
        assert stocks[2]._position is None and stocks[2].current_price is None
        assert stocks[3]._position is not None and stocks[3]._position.average_cost == Decimal("0.00")
        assert str(stocks[3]._position.quantity) == "0.0000" and stocks[3].current_price == "0.00"
        assert stocks[3].total_return == "-"
        assert stocks[4].exchange == "NYSE" and stocks[4]._position.quantity == Decimal("1E-8")
        assert stocks[0].price_1d == "" and stocks[0].price_5d == "No observation"
    assert database.read_bytes() == original


def main():
    root, source, mode, restore_directory = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
    sys.path[:0] = [str(root), str(source)]
    os.environ.pop("FMP_API_KEY", None)
    os.environ.pop("MY_API_KEY", None)
    os.environ["MPLBACKEND"] = "Agg"
    os.environ["MPLCONFIGDIR"] = str(Path.cwd() / "matplotlib")
    os.environ["COLUMNS"] = "300"
    real_open = Path.open
    def no_legacy_data(path, *args, **kwargs):
        if path.suffix == ".pkl":
            return denied()
        return real_open(path, *args, **kwargs)
    with ExitStack() as guards:
        for target, attribute in (
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(Path, "open", no_legacy_data))
        import dotenv
        guards.enter_context(patch.object(dotenv, "load_dotenv", lambda *a, **k: False))
        from stock_tracker.providers import factory
        guards.enter_context(patch.object(factory, "create_market_data_provider", denied))
        # Synthetic controls prove the child process's own guards are active.
        for call in (lambda: pickle.loads(b"synthetic"), lambda: socket.create_connection(("example.invalid", 1)),
                     lambda: (Path.cwd() / "watchlist.pkl").open("rb")):
            try:
                call()
            except AssertionError:
                pass
            else:
                raise AssertionError("M3 subprocess guard was inactive")
        from stock_tracker.persistence.transfer import import_neutral_state, backup_database, restore_database
        database = Path.cwd() / "stock_tracker.sqlite3"
        if mode == "prepare":
            neutral = Path.cwd() / "reviewed-neutral.json"
            neutral.write_text(json.dumps(payload()), encoding="utf-8")
            original = neutral.read_bytes()
            import_neutral_state(neutral, database)
            assert neutral.read_bytes() == original
        elif mode == "copy":
            original = database.read_bytes()
            neutral = Path.cwd() / "reviewed-neutral.json"
            neutral_original = neutral.read_bytes()
            backup = Path.cwd() / "verified-backup.sqlite3"
            backup_database(database, backup)
            restore_database(backup, restore_directory / "stock_tracker.sqlite3")
            assert database.read_bytes() == original
            assert neutral.read_bytes() == neutral_original
        else:
            assert mode == "verify"
            verify(database)
        for name in ("stock_tracker.persistence.transfer", "stock_tracker.persistence.sqlite_portfolios",
                     "stock_tracker.persistence.sqlite_watchlists", "stock_tracker.domain"):
            assert Path(sys.modules[name].__file__).resolve().is_relative_to(source.resolve())
        for name in ("menu_watchlist", "daniils_stock_method"):
            if name in sys.modules:
                assert Path(sys.modules[name].__file__).resolve().is_relative_to(root.resolve())


if __name__ == "__main__":
    main()
