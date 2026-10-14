"""Cold source/wheel current-service imports and use cases under denial guards."""

import builtins
from contextlib import ExitStack
from datetime import datetime, timezone
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
from types import SimpleNamespace
import urllib.request
from unittest.mock import patch


FORBIDDEN = {
    "config", "stock", "watch_list", "menu_watchlist", "daniils_stock_method", "utils",
    "dotenv", "typer", "rich", "matplotlib", "stock_tracker.compatibility", "stock_tracker.cli",
    "stock_tracker.providers.factory", "stock_tracker.providers.fmp", "stock_tracker.providers.transport",
    "stock_tracker.providers.history_cache", "stock_tracker.persistence.sqlite_watchlists",
    "stock_tracker.persistence.sqlite_portfolios", "stock_tracker.persistence.connection",
    "stock_tracker.persistence.migrations", "stock_tracker.persistence.transfer",
    "stock_tracker.persistence.history_cache", "sqlite3", "socket", "urllib", "pickle",
}


def forbidden(name):
    return any(name == item or name.startswith(item + ".") for item in FORBIDDEN)


def denied(*args, **kwargs):
    raise AssertionError("Current service isolation denied external work")


class DeniedEnvironment:
    __getitem__ = get = __iter__ = __contains__ = keys = items = values = denied


class DeniedOutput:
    write = writelines = denied


class DeniedImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if forbidden(fullname):
            denied()
        return None


def main(root):
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
            (os, "open"), (os, "getenv"), (sqlite3, "connect"),
            (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
            (pickle, "load"), (pickle, "loads"), (pickle, "dump"), (pickle, "dumps"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(os, "environ", DeniedEnvironment()))
        guards.enter_context(patch.object(sys, "stdout", DeniedOutput()))
        guards.enter_context(patch.object(sys, "stderr", DeniedOutput()))
        for control in (
            lambda: __import__("rich"), lambda: __import__("config"),
            lambda: importlib.import_module("stock_tracker.providers.factory"),
            lambda: importlib.import_module("stock_tracker.compatibility.numeric"),
            lambda: os.getenv("CURRENT_SERVICE_PROBE"), lambda: os.environ["CURRENT_SERVICE_PROBE"],
            lambda: socket.getaddrinfo("example.invalid", 443), lambda: sqlite3.connect(":memory:"),
            lambda: open("current-service-probe", "w"), lambda: pickle.loads(b"untrusted"),
            lambda: print("current-service-probe"),
        ):
            try:
                control()
            except (AssertionError, ModuleNotFoundError):
                pass
            else:
                raise AssertionError("Current service guard control failed")
        from stock_tracker.services.current_data import CurrentDataService
        from stock_tracker.services.numeric import to_decimal
        from stock_tracker.domain import DomainValidationError
        from stock_tracker.exceptions import ProviderUnavailableError
        from stock_tracker.persistence.models import WatchlistRecord
        from stock_tracker.providers.models import CompanyProfile, InstrumentIdentity, PeriodChanges
        for implementation in (CurrentDataService, to_decimal):
            assert Path(sys.modules[implementation.__module__].__file__).is_relative_to(root)
        stamp = datetime(2020, 1, 1, tzinfo=timezone.utc)
        profile = CompanyProfile("AAPL", "Fictional", "NASDAQ", "USD", None, None, Decimal(120),
                                 Decimal("1000000000.123"), None, stamp)
        periods = PeriodChanges("AAPL", *(Decimal("12.345") for _ in range(8)), None, stamp)
        calls = []
        failure_stage = None
        def source(operation, ordinal, *, on_configuration_failure=None):
            def request(symbol):
                calls.append(operation)
                if operation == failure_stage:
                    raise ProviderUnavailableError()
                return InstrumentIdentity(symbol, "NASDAQ", None, None) if operation == "resolve" else (
                    profile if operation == "profile" else periods)
            return SimpleNamespace(resolve_symbol=request, get_company_profile=request, get_period_changes=request)
        service = CurrentDataService(source)
        original = WatchlistRecord("menu_watchlist", "Probe", ())
        prepared = service.prepare_add(original, "AAPL")
        assert calls == ["resolve", "profile", "periods"]
        try:
            service.validate_ownership("1_0", "100")
        except DomainValidationError:
            pass
        else:
            raise AssertionError("Decorated ownership input accepted")
        ownership = service.validate_ownership("0.12345678901234567890123456789", "100.0000")
        result = service.finish_add(original, prepared, ownership)
        assert original.entries == () and str(result.record.entries[0].quantity) == "0.12345678901234567890123456789"
        assert result.updates[0].profile.market_cap == Decimal("1000000000.123")
        assert result.updates[0].periods.day_1 == Decimal("12.345")
        assert calls == ["resolve", "profile", "periods"]
        events = []
        service.refresh(result.record, on_update=events.append)
        assert len(events) == 2 and events[0].profile is not None and events[1].periods is not None
        failure_stage = "periods"
        events.clear()
        try:
            service.refresh(result.record, on_update=events.append)
        except ProviderUnavailableError:
            pass
        else:
            raise AssertionError("Provider failure was swallowed")
        assert len(events) == 2 and events[-1].invalidate_periods and events[-1].periods is None
        assert result.record.entries[0].current_price == Decimal(120)


if __name__ == "__main__":
    import_root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(import_root))
    main(import_root)
