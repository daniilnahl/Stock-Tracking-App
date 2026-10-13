"""Real SQLite restart and guarded snapshot computation, source or offline wheel."""

from contextlib import ExitStack, closing
from decimal import Decimal
from pathlib import Path
import pickle
import socket
import sqlite3
import sys
import urllib.request
from unittest.mock import patch

# This explicitly loaded test helper is never installed in the application wheel.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from domain_isolation_probe import isolated_domain


def denied(*args, **kwargs):
    raise AssertionError("Analytics restart audit denied network/pickle")


def holdings():
    from stock_tracker.domain import Portfolio, Position, Stock
    first = Position(Stock("A", exchange="NASDAQ"), Decimal("0.2500"), Decimal("100.00"))
    return Portfolio(7, "Synthetic snapshot", [
        first, first,
        Position(Stock("B", exchange="NASDAQ"), Decimal("0.5"), Decimal("200")),
        Position(Stock("A", exchange="NYSE"), Decimal("1"), Decimal("50")),
        Position(Stock("A"), Decimal("0E-30"), Decimal("-0.00")),
        Position(Stock("A"), Decimal("0E-30"),
                 Decimal("100.123456789012345678901234567890")),
    ])


def state(database):
    """Read exact stored inputs/schema outside the pure-calculation boundary."""
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        schema = connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type='table' ORDER BY name").fetchall()
        assert [name for name, _ in schema] == [
            "portfolios", "positions", "watchlist_entries", "watchlists"]
        assert [column[1] for column in connection.execute("PRAGMA table_info(positions)")] == [
            "portfolio_id", "ordinal", "symbol", "name", "exchange", "quantity", "average_cost"]
        assert [column[1] for column in connection.execute("PRAGMA table_info(portfolios)")] == [
            "id", "name"]
        rows = connection.execute(
            "SELECT ordinal,symbol,exchange,quantity,average_cost FROM positions "
            "WHERE portfolio_id=? ORDER BY ordinal", ("7",)).fetchall()
        assert rows == [
            (0, "A", "NASDAQ", "0.2500", "100.00"),
            (1, "A", "NASDAQ", "0.2500", "100.00"),
            (2, "B", "NASDAQ", "0.5", "200"),
            (3, "A", "NYSE", "1", "50"),
            (4, "A", None, "0E-30", "-0.00"),
            (5, "A", None, "0E-30", "100.123456789012345678901234567890"),
        ]
        assert connection.execute("SELECT * FROM watchlists").fetchall() == []
        assert connection.execute("SELECT * FROM watchlist_entries").fetchall() == []
        return schema, rows


def evaluate(saved):
    from stock_tracker.domain import (
        PositionValuationInput, SnapshotCurrencyMismatchError,
        SnapshotCurrencyUnavailableError, portfolio_snapshot,
    )
    assert saved.positions[0].stock == saved.positions[1].stock
    assert saved.positions[0].stock != saved.positions[3].stock
    assert saved.positions[4].stock != saved.positions[5].stock
    assert all(not hasattr(position, "currency") for position in saved.positions)
    assert tuple((position.stock.symbol, position.stock.exchange,
                  str(position.quantity), str(position.average_cost))
                 for position in saved.positions) == (
        ("A", "NASDAQ", "0.2500", "100.00"),
        ("A", "NASDAQ", "0.2500", "100.00"),
        ("B", "NASDAQ", "0.5", "200"),
        ("A", "NYSE", "1", "50"),
        ("A", None, "0E-30", "-0.00"),
        ("A", None, "0E-30", "100.123456789012345678901234567890"),
    )
    before = tuple((position.stock, str(position.quantity), str(position.average_cost))
                   for position in saved.positions)

    def inputs(prices, *, zero_basis=False):
        return tuple(PositionValuationInput(
            position.with_owned_data(position.quantity, Decimal(0)) if zero_basis else position,
            None if price is None else Decimal(price), "USD", "USD",
        ) for position, price in zip(saved.positions, prices))

    observations = ("120", "120", "240", "60", "0", "0")
    supplied = inputs(observations)
    for prices, value, pnl, ratio, weights in (
        (observations, "240", "40", "0.2", ("0.125", "0.125", "0.5", "0.25", "0", "0")),
        (("80", "80", "160", "40", "0", "0"), "160", "-40", "-0.2",
         ("0.125", "0.125", "0.5", "0.25", "0", "0")),
        (("0",) * 6, "0", "-200", "-1", (None,) * 6),
        (observations[:-1] + (None,), None, None, None, (None,) * 6),
    ):
        rows = inputs(prices)
        result = portfolio_snapshot(rows, currency="USD")
        assert result.total_cost_basis == Decimal("200")
        assert (result.total_market_value, result.aggregate_unrealized_pnl,
                result.aggregate_unrealized_return) == tuple(
                    None if item is None else Decimal(item) for item in (value, pnl, ratio))
        assert tuple(item.weight for item in result.positions) == tuple(
            None if item is None else Decimal(item) for item in weights)
        assert len(result.positions) == 6
        assert all(item.input is row for item, row in zip(result.positions, rows))
        assert result.positions[0].snapshot.market_value == Decimal(prices[0]) * Decimal("0.25")
    no_basis = portfolio_snapshot(inputs(observations, zero_basis=True), currency="USD")
    assert no_basis.total_cost_basis == Decimal(0)
    assert no_basis.total_market_value == no_basis.aggregate_unrealized_pnl == Decimal("240")
    assert no_basis.aggregate_unrealized_return is None
    empty = portfolio_snapshot((), currency="USD")
    assert (empty.total_cost_basis, empty.total_market_value, empty.aggregate_unrealized_pnl,
            empty.aggregate_unrealized_return, empty.positions) == (Decimal(0), Decimal(0), Decimal(0), None, ())
    for field in ("cost_currency", "quote_currency"):
        for currency, error in ((None, SnapshotCurrencyUnavailableError),
                                ("EUR", SnapshotCurrencyMismatchError)):
            row = PositionValuationInput(saved.positions[-1], None,
                                         currency if field == "cost_currency" else "USD",
                                         currency if field == "quote_currency" else "USD")
            try:
                portfolio_snapshot(supplied[:-1] + (row,), currency="USD")
            except error as caught:
                assert f"Row 5 {field}" in str(caught) and "EUR" not in str(caught)
            else:
                raise AssertionError("Restored holdings supplied implicit currency evidence")
    first = portfolio_snapshot(supplied, currency="USD")
    repeated = portfolio_snapshot(supplied, currency="USD")
    assert first == repeated and first is not repeated
    assert tuple((position.stock, str(position.quantity), str(position.average_cost))
                 for position in saved.positions) == before


def main():
    root, database, mode = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
    assert database.parent == Path.cwd().resolve()
    sys.path.insert(0, str(root))
    # Cold domain import remains proven independently, before persistence loads.
    with isolated_domain():
        import stock_tracker.domain
        assert Path(stock_tracker.domain.__file__).resolve().is_relative_to(root)
    with ExitStack() as guards:
        guards.enter_context(patch.dict(sys.modules, {name: None for name in (
            "config", "stock", "watch_list", "menu_watchlist", "daniils_stock_method",
            "stock_tracker.providers", "stock_tracker.compatibility", "dotenv", "rich", "typer", "matplotlib",
        )}))
        for target, attribute in (
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        for control in (lambda: pickle.loads(b"synthetic"),
                        lambda: socket.create_connection(("example.invalid", 1))):
            try:
                control()
            except AssertionError:
                pass
            else:
                raise AssertionError("Restart guard was inactive")
        from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
        repository = SQLitePortfolioRepository(database)
        if mode == "write":
            assert not database.exists()
            repository.create(holdings())
        else:
            assert mode == "read" and database.exists()
        original = database.read_bytes()
        original_state = state(database)
        saved = repository.get(7)
        assert saved.id == 7 and saved.name == "Synthetic snapshot"
        for module_name in (
            "stock_tracker.domain", "stock_tracker.domain.analytics",
            "stock_tracker.domain.calculations", "stock_tracker.persistence.sqlite_portfolios",
        ):
            assert Path(sys.modules[module_name].__file__).resolve().is_relative_to(root)
        with isolated_domain():
            evaluate(saved)
        assert state(database) == original_state
        assert database.read_bytes() == original
        assert sorted(path.name for path in database.parent.iterdir()) == [database.name]


if __name__ == "__main__":
    main()
