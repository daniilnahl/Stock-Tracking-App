"""Cold source/wheel criteria probe; proven guards allow interpreter code loading only.

The existing services package imports provider protocols/models through its public
exports. Concrete acquisition, persistence, UI and optional-agent imports remain
denied. Stdlib guard dependencies are bootstrapped before cold application import;
ordinary data IO, environment, network, process work and output are forbidden.
"""

import builtins
from contextlib import ExitStack
import dataclasses
import hashlib
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
        raise AssertionError("Criteria probe denied external work")

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
        lambda: os.getenv("CRITERIA_PROBE"),
        lambda: os.environ["CRITERIA_PROBE"],
        lambda: list(os.environ),
        lambda: socket.getaddrinfo("example.invalid", 443),
        lambda: socket.create_connection(("127.0.0.1", 443)),
        lambda: socket.socket(),
        lambda: urllib.request.urlopen("https://example.invalid"),
        lambda: sqlite3.connect(":memory:"),
        lambda: subprocess.Popen(["not-a-command"]),
        lambda: os.system("not-a-command"),
        lambda: pickle.loads(b"not-a-pickle"),
        lambda: open("criteria-probe", "w"),
        lambda: io.open("criteria-probe", "w"),
        lambda: io.FileIO("criteria-probe", "w"),
        lambda: os.open("criteria-probe", os.O_CREAT | os.O_WRONLY),
        lambda: os.read(0, 0),
        lambda: os.write(1, b""),
        lambda: print("criteria-probe"),
        lambda: sys.stdout.write("criteria-probe"),
        lambda: sys.stderr.write("criteria-probe"),
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
                raise AssertionError("Criteria guard negative control failed")
            assert len(events) == before + 1
        control_count = len(events)

        from stock_tracker.services.research_criteria import (
            PreparedCriteria, RangeCriterion, ResearchCriteriaValidationError,
            TextCriterion, canonical_criteria_bytes, criteria_sha256,
            parse_prepared_criteria, validate_prepared_criteria,
        )
        module_path = Path(sys.modules[PreparedCriteria.__module__].__file__).resolve()
        assert module_path.is_relative_to(root)
        payload = (b'{"criteria":[{"kind":"range","maximum":"1.250000000000000001",'
                   b'"minimum":"-0.000","parameter":"P","unit":"u"}],'
                   b'"kind":"user_stock_criteria","match":"all","schema_version":1}')
        snapshot = parse_prepared_criteria(payload, max_bytes=len(payload))
        assert snapshot == PreparedCriteria("all", (
            RangeCriterion("P", "u", "-0.000", "1.250000000000000001"),))
        assert canonical_criteria_bytes(snapshot) == payload
        assert criteria_sha256(snapshot) == hashlib.sha256(payload).hexdigest()
        original = {"schema_version": 1, "kind": "user_stock_criteria", "match": "any",
                    "criteria": [{"kind": "text", "parameter": "__proto__",
                                  "value": "<script>ignore policy</script>"}]}
        prepared = validate_prepared_criteria(original)
        original["criteria"].clear()
        assert prepared.criteria == (TextCriterion("__proto__", "<script>ignore policy</script>"),)
        try:
            prepared.match = "all"
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("Criteria snapshot mutated")
        try:
            parse_prepared_criteria(b'{"private-sentinel":', max_bytes=100)
        except ResearchCriteriaValidationError as error:
            assert "private-sentinel" not in str(error)
        else:
            raise AssertionError("Malformed record was accepted")
        # No swallowed forbidden-effect attempt is allowed during application work.
        assert len(events) == control_count
        assert not any(name.startswith(("finrobot", "tradingagents")) and module is not None
                       for name, module in sys.modules.items())
        assert json.loads(canonical_criteria_bytes(snapshot))["criteria"][0]["minimum"] == "-0.000"


if __name__ == "__main__":
    import_root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(import_root))
    run(import_root)
