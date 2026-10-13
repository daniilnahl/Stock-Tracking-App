"""Fresh-process service isolation and precise SQLite restart, source or wheel."""

import builtins
from contextlib import ExitStack
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
    "dotenv", "typer", "rich", "matplotlib", "stock_tracker.compatibility",
    "stock_tracker.providers.factory", "stock_tracker.providers.fmp",
    "stock_tracker.providers.transport", "stock_tracker.providers.history_cache",
    "stock_tracker.persistence.sqlite_watchlists", "stock_tracker.persistence.sqlite_portfolios",
    "stock_tracker.persistence.connection", "stock_tracker.persistence.migrations",
    "stock_tracker.persistence.transfer", "stock_tracker.persistence.history_cache",
    "stock_tracker.cli", "sqlite3", "socket", "urllib", "pickle",
}


def forbidden(name):
    return any(name == item or name.startswith(item + ".") for item in FORBIDDEN)


def denied(*args, **kwargs):
    raise AssertionError("Service boundary denied external work")


class DeniedEnvironment:
    __getitem__ = get = __iter__ = __contains__ = keys = items = values = denied


class DeniedOutput:
    write = writelines = denied


class DeniedImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if forbidden(fullname):
            denied()
        return None


def isolation(root):
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
            (sqlite3, "connect"), (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(os, "environ", DeniedEnvironment()))
        guards.enter_context(patch.object(sys, "stdout", DeniedOutput()))
        guards.enter_context(patch.object(sys, "stderr", DeniedOutput()))
        controls = (
            lambda: __import__("rich"), lambda: __import__("stock"),
            lambda: importlib.import_module("stock_tracker.providers.factory"),
            lambda: importlib.import_module("stock_tracker.persistence.sqlite_watchlists"),
            lambda: os.getenv("SERVICE_PROBE"), lambda: os.environ["SERVICE_PROBE"],
            lambda: sqlite3.connect(":memory:"), lambda: socket.getaddrinfo("example.invalid", 443),
            lambda: urllib.request.urlopen("https://example.invalid"),
            lambda: open("service-probe", "w"), lambda: print("service-probe"),
            lambda: pickle.loads(b"untrusted"),
        )
        for control in controls:
            try:
                control()
            except (AssertionError, ModuleNotFoundError):
                pass
            else:
                raise AssertionError("Service isolation control failed")

        from stock_tracker.services import WatchlistService
        from stock_tracker.services import models, protocols
        from stock_tracker.domain import Stock
        from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord
        assert Path(sys.modules[WatchlistService.__module__].__file__).is_relative_to(root)
        assert Path(models.__file__).is_relative_to(root)
        assert Path(protocols.__file__).is_relative_to(root)
        row = WatchlistEntry(Stock("AAPL", exchange="NASDAQ"), Decimal(10), Decimal(100), Decimal(120),
                            *(None for _ in range(12)))
        record = WatchlistRecord("menu_watchlist", "Controlled", (row, row, row))
        class Repository:
            value = None
            def get(self, namespace):
                return self.value
            def save(self, record):
                self.value = record
        repository = Repository()
        service = WatchlistService(repository, namespace="menu_watchlist", legacy_present=lambda: False)
        assert service.load().entries == ()
        service.save(record)
        result = service.view(service.load())
        assert result.entries[0].snapshot.unrealized_return == Decimal("0.2")
        assert result.entries[0].snapshot.market_value == Decimal(1200)
        assert len(service.remove(record, "AAPL").entries) == 1


def restart(root, mode):
    # Explicit production IO is allowed here; provider/network/legacy content is not.
    database = Path.cwd() / "service.sqlite3"
    legacy = Path.cwd() / "opaque.pkl"
    with ExitStack() as guards:
        for target, attribute in (
            (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        real_open = builtins.open
        real_io_open = io.open
        def guarded_open(original):
            def checked(file, *args, **kwargs):
                if isinstance(file, (str, os.PathLike)) and Path(file) == legacy:
                    denied()
                return original(file, *args, **kwargs)
            return checked
        guards.enter_context(patch.object(builtins, "open", guarded_open(real_open)))
        guards.enter_context(patch.object(io, "open", guarded_open(real_io_open)))
        for control in (lambda: socket.getaddrinfo("example.invalid", 443),
                        lambda: pickle.loads(b"untrusted"), lambda: open(legacy, "rb")):
            try:
                control()
            except AssertionError:
                pass
            else:
                raise AssertionError("Restart isolation control failed")
        from stock_tracker.cli.storage import LegacyFilePresence
        from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
        from stock_tracker.services import WatchlistService
        from stock_tracker.domain import Stock
        from stock_tracker.persistence.models import WatchlistEntry, WatchlistRecord
        for implementation in (LegacyFilePresence, SQLiteWatchlistRepository, WatchlistService):
            assert Path(sys.modules[implementation.__module__].__file__).is_relative_to(root)
        for namespace in ("menu_watchlist", "daniils_stock_method"):
            service = WatchlistService(SQLiteWatchlistRepository(database), namespace=namespace,
                                       legacy_present=LegacyFilePresence(legacy))
            if mode == "write":
                assert service.load().entries == ()
                row = WatchlistEntry(Stock("PRECISE", exchange="NASDAQ"),
                                    Decimal("0.12345678901234567890123456789"), Decimal("100.0000000001"),
                                    None, *(None for _ in range(12)))
                unowned = WatchlistEntry(Stock("PRECISE", exchange=None), Decimal(0), None, Decimal(0),
                                        *("" for _ in range(12)))
                service.save(WatchlistRecord(namespace, namespace, (row, row, unowned)))
            else:
                result = service.load()
                assert len(result.entries) == 3 and result.name == namespace
                assert str(result.entries[0].quantity) == "0.12345678901234567890123456789"
                assert str(result.entries[0].average_cost) == "100.0000000001"
                assert result.entries[2].average_cost is None and result.entries[2].current_price == 0
                assert result.entries[2].price_1d == ""
                assert service.view(result).entries[0].snapshot.market_value is None


if __name__ == "__main__":
    import_root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(import_root))
    if sys.argv[2] == "isolation":
        isolation(import_root)
    else:
        restart(import_root, sys.argv[2])
