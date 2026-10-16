"""Explicit browser-profile helper: real launcher, temporary synthetic SQLite only."""

from decimal import Decimal
import builtins
from pathlib import Path
import socket
import sys


def main():
    module_root, state = (Path(value).resolve() for value in sys.argv[1:])
    sys.path.insert(0, str(module_root))
    from stock_tracker.api import launcher
    from stock_tracker.domain import Stock
    from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository

    if not Path(launcher.__file__).resolve().is_relative_to(module_root):
        raise AssertionError("Wrong launcher origin")
    repository = SQLiteWatchlistRepository(state / "holdings.sqlite3")
    metadata = {name: None for name in ("sector", "country", "currency", "market_cap", "price_1d", "price_5d",
                "price_30d", "price_3m", "price_6m", "price_1y", "price_3y", "price_5y")}
    metadata["currency"] = "opaque synthetic label"
    stock = Stock("SYNTH", name="Synthetic local security", exchange="NASDAQ")
    entries = (
        WatchlistEntry(stock, Decimal("0.12345678901234567890123456789"), Decimal("10.0000"), None, **metadata),
        WatchlistEntry(stock, Decimal("0"), None, Decimal("0"), **metadata),
        WatchlistEntry(stock, Decimal("0"), Decimal("0"), Decimal("0"), **metadata),
    )
    repository.save(WatchlistRecord("menu_watchlist", "Synthetic local integration / Menu", entries))
    repository.save(WatchlistRecord("daniils_stock_method", "Synthetic local integration / Method", (entries[2], entries[0])))

    # Negative controls prove provider/configuration and outbound network denial.
    # Native Windows event-loop control sockets may connect only to loopback.
    original_import = builtins.__import__
    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if not level and name in ("config", "dotenv", "stock_tracker.providers.factory", "stock_tracker.providers.fmp", "stock_tracker.providers.transport"):
            raise AssertionError("Provider acquisition denied")
        return original_import(name, globals, locals, fromlist, level)
    builtins.__import__ = guarded_import
    def network_guard(event, args):
        if event == "socket.connect" and (not isinstance(args[1], tuple) or args[1][0] not in ("127.0.0.1", "::1")):
            raise AssertionError("Outbound network denied")
        if event == "socket.getaddrinfo" and args[0] not in ("127.0.0.1", "localhost", "::1"):
            raise AssertionError("Outbound DNS denied")
    sys.addaudithook(network_guard)
    for control in (lambda: __import__("config"), lambda: socket.getaddrinfo("outside.invalid", 443)):
        try:
            control()
        except AssertionError:
            pass
        else:
            raise AssertionError("Guard control failed")
    return launcher.main(["--database", str(state / "holdings.sqlite3"), "--history-cache", str(state / "history.json"),
        "--menu-legacy", str(state / "menu.pkl"), "--evaluation-legacy", str(state / "method.pkl"), "--dashboard"])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        # No raw diagnostics, paths or environment values enter browser reports.
        sys.stderr.write("Synthetic launcher fixture failed.\n")
        raise SystemExit(1) from None
