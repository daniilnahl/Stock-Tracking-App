"""Fresh source/wheel history service execution with external boundaries denied."""

import builtins
from contextlib import ExitStack
from datetime import date, datetime, timezone
from decimal import Decimal
import importlib.abc
import importlib.util
import io
import os
from pathlib import Path
import pickle
import socket
import sqlite3
import sys
import urllib.request
from unittest.mock import patch


FORBIDDEN = {
    "config", "stock", "watch_list", "menu_watchlist", "daniils_stock_method", "utils",
    "dotenv", "typer", "rich", "matplotlib", "stock_tracker.compatibility", "stock_tracker.cli",
    "stock_tracker.providers.factory", "stock_tracker.providers.fmp", "stock_tracker.providers.transport",
    "stock_tracker.providers.history_cache", "stock_tracker.persistence.connection",
    "stock_tracker.persistence.sqlite_watchlists", "stock_tracker.persistence.sqlite_portfolios",
    "stock_tracker.persistence.migrations", "stock_tracker.persistence.transfer",
    "stock_tracker.persistence.history_cache", "sqlite3", "socket", "urllib", "pickle",
}


def forbidden(name):
    return any(name == item or name.startswith(item + ".") for item in FORBIDDEN)


def denied(*args, **kwargs):
    raise AssertionError("History service boundary denied external work")


class DeniedEnvironment:
    __getitem__ = get = __iter__ = __contains__ = keys = items = values = denied


class DeniedOutput:
    write = writelines = denied


class DeniedImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if forbidden(fullname):
            denied()
        return None


def run(root):
    original_import = builtins.__import__
    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        resolved = importlib.util.resolve_name("." * level + name, globals["__package__"]) if level else name
        if forbidden(resolved):
            denied()
        return original_import(name, globals, locals, fromlist, level)
    with ExitStack() as guards:
        blocked = {name: None for name in sys.modules if forbidden(name)}
        blocked.update({name: None for name in FORBIDDEN})
        guards.enter_context(patch.dict(sys.modules, blocked))
        guards.enter_context(patch.object(builtins, "__import__", guarded_import))
        guards.enter_context(patch.object(sys, "meta_path", [DeniedImports(), *sys.meta_path]))
        for target, attribute in (
            (builtins, "open"), (builtins, "print"), (io, "open"), (io, "FileIO"),
            (os, "open"), (os, "getenv"), (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (sqlite3, "connect"), (urllib.request, "urlopen"), (pickle, "load"), (pickle, "loads"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(os, "environ", DeniedEnvironment()))
        guards.enter_context(patch.object(sys, "stdout", DeniedOutput()))
        guards.enter_context(patch.object(sys, "stderr", DeniedOutput()))
        for control in (lambda: __import__("rich"), lambda: __import__("stock"),
                        lambda: importlib.import_module("stock_tracker.providers.factory"),
                        lambda: os.environ["PROBE"], lambda: os.getenv("PROBE"),
                        lambda: sqlite3.connect(":memory:"), lambda: socket.getaddrinfo("example.invalid", 443),
                        lambda: urllib.request.urlopen("https://example.invalid"),
                        lambda: open("history-probe", "w"), lambda: print("history-probe"),
                        lambda: pickle.loads(b"untrusted")):
            try:
                control()
            except (AssertionError, ModuleNotFoundError):
                pass
            else:
                raise AssertionError("History boundary control failed")

        from stock_tracker.domain import Stock
        from stock_tracker.providers.models import PriceBar
        from stock_tracker.services import HistoryService
        from stock_tracker.services import history_policy
        for implementation in (HistoryService, PriceBar):
            assert Path(sys.modules[implementation.__module__].__file__).is_relative_to(root)
        assert Path(history_policy.__file__).is_relative_to(root)
        now = datetime(2020, 3, 1, tzinfo=timezone.utc)
        first, last = date(2020, 1, 2), date(2020, 1, 6)
        bars = [PriceBar("AAPL", first, Decimal(100), Decimal(120), Decimal(99),
                         Decimal("110.0000000000000000001"), None, 0)]
        calls = []
        class Provider:
            def get_price_history(self, symbol, start, end):
                calls.append((symbol, start, end))
                return bars
        def source(ordinal):
            assert ordinal == 3
            return Provider()
        service = HistoryService(source, clock=lambda: now)
        stock = Stock("AAPL", exchange="NASDAQ")
        result = service.history(stock, ordinal=3, start=first, end=last)
        assert result.stock is stock and result.bars == tuple(bars)
        assert result.bars[0].close == Decimal("110.0000000000000000001")
        assert (result.start, result.end) == (first, last)
        assert calls == [("AAPL", first, last)]
        bars.clear()
        assert len(result.bars) == 1


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root))
    run(root)
