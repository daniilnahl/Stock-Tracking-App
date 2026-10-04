"""Independent subprocess guards and domain behavior, for source or installed code.

Run with Python -I and an explicit application import root. Only this test helper
preloads infrastructure stdlib to install guards; no legacy application is loaded.
"""

import builtins
from contextlib import ExitStack
import dataclasses
from decimal import Decimal
import importlib.abc
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
    "config", "stock", "watch_list", "menu_watchlist", "daniils_stock_method",
    "utils", "dotenv", "rich", "typer", "matplotlib", "urllib", "socket",
    "sqlite3", "stock_tracker.compatibility", "stock_tracker.providers", "stock_tracker.exceptions",
}


def is_forbidden(name):
    return any(name == item or name.startswith(item + ".") for item in FORBIDDEN)


def denied(*args, **kwargs):
    raise AssertionError("Domain isolation guard denied infrastructure work")


class DeniedEnvironment:
    __getitem__ = get = __iter__ = __contains__ = keys = items = values = denied


class DeniedOutput:
    write = writelines = denied


class DeniedImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if is_forbidden(fullname):
            denied()
        return None


def main(import_root):
    root = Path(import_root).resolve()
    sys.path.insert(0, str(root))
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        resolved = importlib.util.resolve_name("." * level + name, globals["__package__"]) if level else name
        if is_forbidden(resolved):
            denied()
        return original_import(name, globals, locals, fromlist, level)

    # References are captured before forbidden modules are made unavailable.
    probes = (
        lambda: __import__("stock"),
        lambda: __import__("stock_operations", {"__package__": "stock_tracker.compatibility"}, level=1),
        lambda: importlib.import_module("stock_tracker.compatibility"),
        lambda: importlib.import_module("stock_tracker.providers"),
        lambda: importlib.import_module("stock_tracker.exceptions"),
        lambda: os.getenv("DOMAIN_ISOLATION_PROBE"),
        lambda: os.environ["DOMAIN_ISOLATION_PROBE"],
        lambda: list(os.environ),
        lambda: socket.getaddrinfo("example.invalid", 443),
        lambda: socket.create_connection(("127.0.0.1", 443)),
        lambda: sqlite3.connect(":memory:"),
        lambda: urllib.request.urlopen("https://example.invalid/"),
        lambda: open("domain-probe", "w"),
        lambda: io.open("domain-probe", "w"),
        lambda: io.FileIO("domain-probe", "w"),
        lambda: os.open("domain-probe", os.O_CREAT | os.O_WRONLY),
        lambda: os.read(0, 0),
        lambda: os.write(1, b""),
        lambda: print("domain-probe"),
        lambda: sys.stdout.write("domain-probe"),
        lambda: sys.stderr.write("domain-probe"),
    )
    blocked = {name: None for name in sys.modules if is_forbidden(name)}
    blocked.update({name: None for name in FORBIDDEN})
    with ExitStack() as guards:
        guards.enter_context(patch.dict(sys.modules, blocked))
        guards.enter_context(patch.object(builtins, "__import__", guarded_import))
        guards.enter_context(patch.object(sys, "meta_path", [DeniedImports(), *sys.meta_path]))
        for target, attribute in (
            (builtins, "open"), (builtins, "print"), (io, "open"), (io, "FileIO"),
            (os, "open"), (os, "read"), (os, "write"),
            (os, "getenv"), (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"),
            (socket.socket, "sendto"), (urllib.request, "urlopen"),
            (urllib.request.OpenerDirector, "open"), (sqlite3, "connect"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(os, "environ", DeniedEnvironment()))
        guards.enter_context(patch.object(sys, "stdout", DeniedOutput()))
        guards.enter_context(patch.object(sys, "stderr", DeniedOutput()))
        for probe in probes:
            try:
                probe()
            except (AssertionError, ModuleNotFoundError):
                pass
            else:
                raise AssertionError("An isolation probe reached prohibited work")

        from stock_tracker.domain import (
            DomainValidationError, Portfolio, Position, PositionSnapshot, Stock,
            position_snapshot,
        )

        stock = Stock("AAPL", exchange="NASDAQ")
        assert stock == Stock("AAPL", name="Apple", exchange="NASDAQ")
        assert stock != Stock("AAPL", exchange="NYSE")
        assert Stock("AAPL") != Stock("AAPL")
        position = Position(stock, Decimal("0.25"), Decimal("100"))
        replacement = position.with_owned_data(Decimal("2"), Decimal("3"))
        supplied = [position, replacement, position]
        portfolio = Portfolio(None, "Example", supplied)
        assert portfolio.positions == supplied and portfolio.positions is not supplied
        supplied.clear()
        assert portfolio.positions == [position, replacement, position]
        assert Portfolio(None, "Other").positions == []
        result = position_snapshot(position, Decimal("120"))
        assert isinstance(result, PositionSnapshot)
        assert dataclasses.astuple(result) == (
            Decimal("25"), Decimal("30"), Decimal("5"), Decimal("0.20"),
        )
        missing = position_snapshot(position, None)
        assert dataclasses.astuple(missing) == (Decimal("25"), None, None, None)
        zero = position_snapshot(position.with_owned_data(Decimal("0"), Decimal("100")), Decimal("120"))
        assert dataclasses.astuple(zero) == (Decimal("0"), Decimal("0"), Decimal("0"), None)
        assert position.quantity == Decimal("0.25") and replacement.stock is stock
        assert issubclass(DomainValidationError, ValueError)
        for item in (Stock, Position, Portfolio, PositionSnapshot, position_snapshot, DomainValidationError):
            assert Path(sys.modules[item.__module__].__file__).resolve().is_relative_to(root)
        assert all(module is None for name, module in sys.modules.items() if is_forbidden(name))


if __name__ == "__main__":
    main(sys.argv[1])
