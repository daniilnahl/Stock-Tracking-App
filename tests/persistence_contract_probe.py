"""Fresh source/wheel storage contract probe with infrastructure access denied."""

import builtins
from contextlib import ExitStack
from decimal import Decimal
import importlib.util
import io
import os
from pathlib import Path
import socket
import sqlite3
import sys
import urllib.request
from unittest.mock import patch


FORBIDDEN = {
    "stock", "watch_list", "menu_watchlist", "daniils_stock_method", "config", "utils",
    "stock_tracker.providers", "stock_tracker.compatibility", "dotenv", "rich", "typer",
    "matplotlib", "urllib", "socket", "sqlite3",
}


def denied(*args, **kwargs):
    raise AssertionError("Persistence contracts attempted infrastructure access")


def forbidden(name):
    return any(name == item or name.startswith(item + ".") for item in FORBIDDEN)


def main(import_root):
    root = Path(import_root).resolve()
    sys.path.insert(0, str(root))
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        resolved = importlib.util.resolve_name("." * level + name, globals["__package__"]) if level else name
        if forbidden(resolved):
            denied()
        return original_import(name, globals, locals, fromlist, level)

    class DeniedEnvironment:
        __getitem__ = get = __iter__ = __contains__ = keys = items = values = denied

    blocked = {name: None for name in sys.modules if forbidden(name)}
    blocked.update({name: None for name in FORBIDDEN})
    with ExitStack() as guards:
        guards.enter_context(patch.dict(sys.modules, blocked))
        guards.enter_context(patch.object(builtins, "__import__", guarded_import))
        for target, attribute in (
            (builtins, "open"), (builtins, "print"), (io, "open"), (io, "FileIO"),
            (os, "open"), (os, "getenv"), (sqlite3, "connect"),
            (socket, "create_connection"), (socket.socket, "connect"),
            (urllib.request, "urlopen"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(os, "environ", DeniedEnvironment()))
        for check in (lambda: os.getenv("PERSISTENCE_PROBE"), lambda: sqlite3.connect(":memory:"),
                      lambda: __import__("config"), lambda: open("probe", "w")):
            try:
                check()
            except (AssertionError, ModuleNotFoundError):
                pass
            else:
                raise AssertionError("Isolation selfcheck failed")

        from stock_tracker.domain import Portfolio, Stock
        from stock_tracker.exceptions import PersistenceValidationError
        from stock_tracker.persistence import (
            PortfolioRepository, WatchlistEntry, WatchlistRecord, WatchlistRepository,
        )

        item = WatchlistEntry(Stock("aapl"), Decimal("0"), None, None,
                             *([None] * 12))
        record = WatchlistRecord("menu_watchlist", "Watchlist", (item, item))
        assert len(record.entries) == 2 and record.entries[0] is record.entries[1]
        assert item.average_cost is None and item.current_price is None
        assert Portfolio(-1, "Example").id == -1
        try:
            WatchlistEntry(item.stock, True, None, None, *([None] * 12))
        except PersistenceValidationError:
            pass
        else:
            raise AssertionError("Invalid numeric input accepted")
        for name in ("stock_tracker.persistence", WatchlistEntry.__module__,
                     WatchlistRecord.__module__, PortfolioRepository.__module__,
                     WatchlistRepository.__module__, PersistenceValidationError.__module__):
            assert Path(sys.modules[name].__file__).resolve().is_relative_to(root)


if __name__ == "__main__":
    main(sys.argv[1])
