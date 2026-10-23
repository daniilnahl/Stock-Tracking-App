"""Cold source/wheel holdings projection probe; proven guards allow interpreter code loading only.

The existing services package imports provider protocols/models through its public
exports. Concrete acquisition, persistence, UI and optional-agent imports remain
denied. Stdlib guard dependencies are bootstrapped before cold application import;
ordinary data IO, environment, network, process work and output are forbidden.
"""

import builtins
from contextlib import ExitStack
from decimal import Decimal
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path
import pickle
import socket
import sqlite3
import subprocess
import sys
import urllib.request
from unittest.mock import patch


FORBIDDEN = {
    "config", "stock", "watch_list", "menu_watchlist", "daniils_stock_method", "utils",
    "dotenv", "rich", "typer", "matplotlib", "finrobot", "tradingagents", "langchain",
    "pydantic_ai", "keyring", "ctypes", "stock_tracker.api", "stock_tracker.cli",
    "stock_tracker.compatibility", "stock_tracker.providers.factory",
    "stock_tracker.providers.finnhub_factory", "stock_tracker.providers.fmp",
    "stock_tracker.providers.finnhub", "stock_tracker.providers.transport",
    "stock_tracker.providers.finnhub_transport", "stock_tracker.providers.history_cache",
    "stock_tracker.persistence.connection", "stock_tracker.persistence.sqlite_watchlists",
    "stock_tracker.persistence.sqlite_portfolios", "stock_tracker.persistence.migrations",
    "stock_tracker.persistence.transfer", "stock_tracker.persistence.history_cache",
    "socket", "sqlite3", "urllib", "subprocess", "pickle",
}


def forbidden(name):
    return any(name == prefix or name.startswith(prefix + ".") for prefix in FORBIDDEN)


def run(root):
    events = []

    def denied(*args, **kwargs):
        events.append("denied")
        raise AssertionError("Holdings probe denied external work")

    class Imports(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if forbidden(fullname):
                denied()
            return None

    class Environment:
        get = __getitem__ = __iter__ = __contains__ = keys = items = values = denied

    class Output:
        write = writelines = denied

    original_import = builtins.__import__
    original_import_module = importlib.import_module

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        resolved = importlib.util.resolve_name("." * level + name, globals["__package__"]) if level else name
        if forbidden(resolved):
            denied()
        return original_import(name, globals, locals, fromlist, level)

    def guarded_import_module(name, package=None):
        resolved = importlib.util.resolve_name(name, package) if name.startswith(".") else name
        if forbidden(resolved):
            denied()
        return original_import_module(name, package)

    controls = (
        lambda: __import__("config"),
        lambda: importlib.import_module("stock_tracker.providers.fmp"),
        lambda: importlib.import_module("finrobot"),
        lambda: os.getenv("HOLDINGS_PROBE"),
        lambda: os.environ["HOLDINGS_PROBE"],
        lambda: list(os.environ),
        lambda: socket.getaddrinfo("example.invalid", 443),
        lambda: socket.create_connection(("127.0.0.1", 443)),
        lambda: socket.socket(),
        lambda: urllib.request.urlopen("https://example.invalid"),
        lambda: sqlite3.connect(":memory:"),
        lambda: subprocess.Popen(["not-a-command"]),
        lambda: os.system("not-a-command"),
        lambda: pickle.loads(b"not-a-pickle"),
        lambda: open("holdings-probe", "w"),
        lambda: io.open("holdings-probe", "w"),
        lambda: io.FileIO("holdings-probe", "w"),
        lambda: os.open("holdings-probe", os.O_CREAT | os.O_WRONLY),
        lambda: os.read(0, 0),
        lambda: os.write(1, b""),
        lambda: print("holdings-probe"),
        lambda: sys.stdout.write("holdings-probe"),
        lambda: sys.stderr.write("holdings-probe"),
    )
    with ExitStack() as guards:
        blocked = {name: None for name in sys.modules if forbidden(name)}
        blocked.update({name: None for name in FORBIDDEN})
        guards.enter_context(patch.dict(sys.modules, blocked))
        guards.enter_context(patch.object(builtins, "__import__", guarded_import))
        guards.enter_context(patch.object(importlib, "import_module", guarded_import_module))
        guards.enter_context(patch.object(sys, "meta_path", [Imports(), *sys.meta_path]))
        for target, attribute in (
            (builtins, "open"), (builtins, "print"), (io, "open"), (io, "FileIO"),
            (os, "open"), (os, "read"), (os, "write"), (os, "getenv"), (os, "system"),
            (socket, "getaddrinfo"), (socket, "create_connection"), (socket, "socket"),
            (sqlite3, "connect"), (urllib.request, "urlopen"),
            (urllib.request.OpenerDirector, "open"), (subprocess, "Popen"),
            (pickle, "loads"), (pickle, "load"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(os, "environ", Environment()))
        guards.enter_context(patch.object(sys, "stdout", Output()))
        guards.enter_context(patch.object(sys, "stderr", Output()))
        for control in controls:
            before = len(events)
            try:
                control()
            except (AssertionError, ModuleNotFoundError):
                pass
            else:
                raise AssertionError("Holdings guard negative control failed")
            assert len(events) == before + 1
        control_count = len(events)

        from stock_tracker.domain import Position, PositionValuationInput, Stock, SnapshotCurrencyUnavailableError
        from stock_tracker.services.research_holdings import ResearchHoldingsValidationError, project_holdings
        module_path = Path(sys.modules[project_holdings.__module__].__file__).resolve()
        assert module_path.is_relative_to(root)
        first = PositionValuationInput(Position(Stock("A", name="PRIVATE-NAME", exchange="NASDAQ"),
                                                Decimal("10"), Decimal("100")),
                                        Decimal("120"), "USD", "USD")
        second = PositionValuationInput(Position(Stock("B", exchange=None), Decimal("5"), Decimal("40")),
                                         Decimal("60"), "USD", "USD")
        payload = project_holdings((first, second), currency="USD", max_rows=2, max_output_bytes=1000)
        assert payload == b'[{"portfolio_weight":"0.8","ticker":"A"},{"portfolio_weight":"0.2","ticker":"B"}]'
        assert b"PRIVATE" not in payload and b"exchange" not in payload
        assert all(set(item) == {"ticker", "portfolio_weight"} for item in json.loads(payload))
        duplicates = project_holdings((first, first), currency="USD", max_rows=2, max_output_bytes=1000)
        assert duplicates == b'[{"portfolio_weight":"0.5","ticker":"A"},{"portfolio_weight":"0.5","ticker":"A"}]'
        assert project_holdings((), currency="USD", max_rows=1, max_output_bytes=2) == b"[]"
        missing = PositionValuationInput(Position(Stock("C"), Decimal(0), Decimal(0)), None, "USD", "USD")
        nulls = project_holdings((first, missing), currency="USD", max_rows=2, max_output_bytes=1000)
        assert [item["portfolio_weight"] for item in json.loads(nulls)] == [None, None]
        unknown = PositionValuationInput(first.position, first.current_price, None, "USD")
        try:
            project_holdings((unknown,), currency="USD", max_rows=1, max_output_bytes=1000)
        except SnapshotCurrencyUnavailableError:
            pass
        else:
            raise AssertionError("Unknown currency was assumed")
        try:
            project_holdings((first,), currency="USD", max_rows=True, max_output_bytes=1000)
        except ResearchHoldingsValidationError as error:
            assert error.__cause__ is error.__context__ is None
        else:
            raise AssertionError("Invalid caller bound was accepted")
        assert first.position.quantity == Decimal("10") and first.position.average_cost == Decimal("100")
        assert first.position.stock.exchange == "NASDAQ"
        # Detect an external-work attempt even if application code swallows it.
        assert len(events) == control_count
        assert not any(name.startswith(("finrobot", "tradingagents")) and module is not None
                       for name, module in sys.modules.items())


if __name__ == "__main__":
    import_root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(import_root))
    run(import_root)
