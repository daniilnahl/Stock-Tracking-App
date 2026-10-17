"""Cold source/wheel EPS service execution with proven external-work guards."""

import builtins
from contextlib import ExitStack
from datetime import date, datetime, timezone
from decimal import Decimal
import importlib.abc
import importlib.util
import io
import os
from pathlib import Path
import socket
import sqlite3
import sys
from types import SimpleNamespace
import urllib.request
from unittest.mock import patch


FORBIDDEN = {
    "config", "stock", "utils", "dotenv", "typer", "rich", "matplotlib",
    "stock_tracker.compatibility", "stock_tracker.cli", "stock_tracker.api",
    "stock_tracker.providers.factory", "stock_tracker.providers.fmp",
    "stock_tracker.providers.finnhub", "stock_tracker.providers.finnhub_transport",
    "stock_tracker.providers.transport", "stock_tracker.providers.history_cache",
    "stock_tracker.persistence.connection", "stock_tracker.persistence.sqlite_watchlists",
    "stock_tracker.persistence.sqlite_portfolios", "stock_tracker.persistence.migrations",
    "stock_tracker.persistence.transfer", "stock_tracker.persistence.history_cache",
    "sqlite3", "socket", "urllib",
}


def forbidden(name):
    return any(name == item or name.startswith(item + ".") for item in FORBIDDEN)


def denied(*args, **kwargs):
    raise AssertionError("EPS service boundary denied external work")


class DeniedEnvironment:
    __getitem__ = get = __iter__ = __contains__ = keys = items = values = denied


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
            (builtins, "open"), (io, "open"), (io, "FileIO"), (os, "open"), (os, "getenv"),
            (socket, "getaddrinfo"), (socket, "create_connection"), (socket.socket, "connect"),
            (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (sqlite3, "connect"), (urllib.request, "urlopen"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(os, "environ", DeniedEnvironment()))
        for control in (
            lambda: __import__("config"), lambda: importlib.import_module("stock_tracker.providers.finnhub"),
            lambda: os.environ["EPS_SERVICE_PROBE"], lambda: os.getenv("EPS_SERVICE_PROBE"),
            lambda: sqlite3.connect(":memory:"), lambda: socket.getaddrinfo("example.invalid", 443),
            lambda: urllib.request.urlopen("https://example.invalid"), lambda: open("eps-service-probe", "w"),
        ):
            try:
                control()
            except (AssertionError, ModuleNotFoundError):
                pass
            else:
                raise AssertionError("EPS service boundary control failed")
        from stock_tracker.providers.eps import UpcomingEpsEstimate
        from stock_tracker.services import UpcomingEpsService, UpcomingEpsView
        for implementation in (UpcomingEpsEstimate, UpcomingEpsService, UpcomingEpsView):
            assert Path(sys.modules[implementation.__module__].__file__).resolve().is_relative_to(root)
        analysis, first, last = date(2026, 10, 16), date(2026, 10, 17), date(2026, 10, 31)
        observations = (UpcomingEpsEstimate("TEST", 2026, 3, first, None,
                        Decimal("1.250000000000000001"), datetime(2026, 10, 16, tzinfo=timezone.utc)),)
        events = []
        def research_date():
            events.append("date")
            return analysis
        def provider():
            events.append("provider")
            def upcoming(symbol, **kwargs):
                events.append((symbol, kwargs))
                return observations
            return SimpleNamespace(get_upcoming_eps=upcoming)
        service = UpcomingEpsService(provider, research_date=research_date)
        assert events == []
        result = service.upcoming_eps("TEST", start=first, end=last)
        assert isinstance(result, UpcomingEpsView) and result.observations is observations
        assert result.observations[0].estimate == Decimal("1.250000000000000001")
        assert result.observations[0].currency is result.observations[0].share_basis is None
        assert (result.symbol, result.analysis_date, result.start, result.end) == ("TEST", analysis, first, last)
        assert events == ["date", "provider", ("TEST", dict(start=first, end=last, analysis_date=analysis))]


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root))
    run(root)
