"""Independent source/wheel restart check with local-only persistence guards."""

from contextlib import ExitStack
from decimal import Decimal
from pathlib import Path
import pickle
import socket
import sys
import urllib.request
from unittest.mock import patch


def denied(*args, **kwargs):
    raise AssertionError("Network/pickle access denied")


def main():
    root, database, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    sys.path.insert(0, str(root))
    with ExitStack() as guards:
        guards.enter_context(patch.dict(sys.modules, {name: None for name in (
            "config", "stock", "watch_list", "menu_watchlist", "daniils_stock_method",
            "stock_tracker.providers", "dotenv", "rich", "typer", "matplotlib",
        )}))
        for target, attribute in (
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        from stock_tracker.domain import Portfolio, Position, Stock
        from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
        repository = SQLitePortfolioRepository(database)
        huge = 10 ** 4500
        if mode == "write":
            assert repository.get(huge) is None and repository.list() == []
            assert not database.exists()
            holding = Position(Stock("AAPL", name="Exact", exchange="NASDAQ"),
                               Decimal("0.123456789012345678901234567890123456789"),
                               Decimal("100.0000000000000000000000000000000001"))
            candidate = Portfolio(huge, "Restart", [holding, holding,
                                  Position(Stock("AAPL"), Decimal("0E-30"), Decimal("-0.00"))])
            result = repository.create(candidate)
            assert result.id == huge and result.positions is not candidate.positions
            assert repository.create(Portfolio(None, "Allocated")).id == huge + 1
        else:
            assert mode == "read"
            saved = repository.get(huge)
            assert saved.name == "Restart" and len(saved.positions) == 3
            assert saved.positions[0].stock == saved.positions[1].stock
            assert saved.positions[2].stock.exchange is None
            assert str(saved.positions[0].quantity) == "0.123456789012345678901234567890123456789"
            assert str(saved.positions[0].average_cost) == "100.0000000000000000000000000000000001"
            assert str(saved.positions[2].quantity) == "0E-30"
            assert str(saved.positions[2].average_cost) == "-0.00"
            assert [item.id for item in repository.list()] == [huge, huge + 1]
        for name in ("stock_tracker.domain", "stock_tracker.persistence.sqlite_portfolios"):
            assert Path(sys.modules[name].__file__).resolve().is_relative_to(root.resolve())


if __name__ == "__main__":
    main()
