"""Fresh source/wheel provider-contract import and constructor isolation probe."""

import builtins
from contextlib import ExitStack
import datetime as dates
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
    "stock", "watch_list", "menu_watchlist", "daniils_stock_method", "config", "utils",
    "stock_tracker.domain", "stock_tracker.compatibility", "dotenv", "rich", "typer",
    "matplotlib", "urllib", "socket", "sqlite3",
}


def denied(*args, **kwargs):
    raise AssertionError("Provider contract attempted infrastructure or clock access")


def is_forbidden(name):
    return any(name == item or name.startswith(item + ".") for item in FORBIDDEN)


class DeniedImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if is_forbidden(fullname):
            denied()
        return None


class DeniedEnvironment:
    __getitem__ = get = __iter__ = __contains__ = keys = items = values = denied


class DeniedOutput:
    write = writelines = denied


REAL_DATE = dates.date
REAL_DATETIME = dates.datetime


class DateType(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, REAL_DATE)


class DatetimeType(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, REAL_DATETIME)


class GuardedDate(REAL_DATE, metaclass=DateType):
    today = denied


class GuardedDatetime(REAL_DATETIME, metaclass=DatetimeType):
    now = utcnow = today = denied


def main(import_root):
    root = Path(import_root).resolve()
    sys.path.insert(0, str(root))
    received = REAL_DATETIME(2020, 1, 2, tzinfo=dates.timezone.utc)
    session = REAL_DATE(2020, 1, 2)
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        resolved = importlib.util.resolve_name("." * level + name, globals["__package__"]) if level else name
        if is_forbidden(resolved):
            denied()
        return original_import(name, globals, locals, fromlist, level)

    blocked = {name: None for name in sys.modules if is_forbidden(name)}
    blocked.update({name: None for name in FORBIDDEN})
    with ExitStack() as guards:
        guards.enter_context(patch.dict(sys.modules, blocked))
        guards.enter_context(patch.object(builtins, "__import__", guarded_import))
        guards.enter_context(patch.object(sys, "meta_path", [DeniedImports(), *sys.meta_path]))
        for target, attribute in (
            (builtins, "open"), (builtins, "print"), (io, "open"), (io, "FileIO"),
            (os, "open"), (os, "getenv"), (socket, "getaddrinfo"),
            (socket, "create_connection"), (socket.socket, "connect"),
            (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (sqlite3, "connect"), (urllib.request, "urlopen"),
            (urllib.request.OpenerDirector, "open"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(os, "environ", DeniedEnvironment()))
        guards.enter_context(patch.object(sys, "stdout", DeniedOutput()))
        guards.enter_context(patch.object(sys, "stderr", DeniedOutput()))
        guards.enter_context(patch.object(dates, "date", GuardedDate))
        guards.enter_context(patch.object(dates, "datetime", GuardedDatetime))

        for probe in (
            lambda: __import__("urllib.request", fromlist=("Request",)),
            lambda: __import__("domain", {"__package__": "stock_tracker"}, level=1),
            lambda: os.getenv("PROVIDER_CONTRACT_PROBE"),
            lambda: socket.create_connection(("127.0.0.1", 443)),
            lambda: dates.datetime.now(),
            lambda: dates.date.today(),
        ):
            try:
                probe()
            except (AssertionError, ModuleNotFoundError):
                pass
            else:
                raise AssertionError("An isolation selfcheck reached prohibited work")

        from stock_tracker.exceptions import ProviderResponseError, RateLimitError
        from stock_tracker.providers import (
            CompanyProfile, HistoricalMarketDataProvider, InstrumentIdentity,
            MarketDataProvider, PeriodChanges, PriceBar, Quote,
        )

        assert InstrumentIdentity("AAPL", None, None, None).currency is None
        assert Quote("AAPL", Decimal("0"), None, None, None, received).price == Decimal("0")
        assert Quote("AAPL", None, None, None, None, received).as_of is None
        assert CompanyProfile("AAPL", "Fictional", None, None, None, None,
                              None, None, None, received).market_cap is None
        assert PeriodChanges("AAPL", Decimal("-12.5"), None, None, None, None,
                             None, None, None, None, received).day_1 == Decimal("-12.5")
        assert PriceBar("AAPL", session, Decimal("0"), Decimal("0"), Decimal("0"),
                        Decimal("0"), None, 0).date is session
        assert str(RateLimitError(retry_after_seconds=0.0)) == "Market-data rate limit reached."
        try:
            Quote("AAPL", True, None, None, None, received)
        except ProviderResponseError:
            pass
        else:
            raise AssertionError("Invalid numeric input was accepted")
        for name in ("stock_tracker.providers", InstrumentIdentity.__module__,
                     MarketDataProvider.__module__, HistoricalMarketDataProvider.__module__,
                     ProviderResponseError.__module__):
            assert Path(sys.modules[name].__file__).resolve().is_relative_to(root)


if __name__ == "__main__":
    main(sys.argv[1])
