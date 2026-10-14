"""Bounded architecture checks, complemented by cold runtime denial probes."""

import ast
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
NEUTRAL = ("stock_tracker.services", "stock_tracker.domain", "stock_tracker.exceptions",
           "stock_tracker.providers.models", "stock_tracker.providers.protocols",
           "stock_tracker.persistence.models", "stock_tracker.persistence.protocols")
CONCRETE = {"os", "sys", "pathlib", "io", "sqlite3", "socket", "urllib", "http", "ssl",
            "pickle", "subprocess", "importlib", "ctypes"}
COMMAND_METHODS = {"get_stock_info", "get_price_over_time", "get_price_history", "get_quote",
                   "get_company_profile", "get_period_changes", "refresh_stocks", "graph_stock",
                   "check_stock_existance", "get_jsonparsed_data", "urlopen", "execute", "connect",
                   "create_market_data_provider", "create_historical_market_data_provider"}


def findings(source, *, service):
    """Detect ordinary imports/calls, not dynamic obfuscation or arbitrary Python."""
    tree, result = ast.parse(source), []
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom):
            module = ("stock_tracker.services." if node.level else "") + (node.module or "")
            modules = [module + "." + item.name for item in node.names]
        for module in modules:
            root = module.split(".")[0]
            if service:
                pure = root in sys.stdlib_module_names and root not in CONCRETE
                if not pure and not any(module == prefix or module.startswith(prefix + ".") for prefix in NEUTRAL):
                    result.append((node.lineno, "service imports infrastructure/presentation"))
            elif root in CONCRETE - {"pathlib"} or module.startswith("stock_tracker.providers."):
                result.append((node.lineno, "command imports concrete infrastructure"))
        if not service and isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else (
                node.func.id if isinstance(node.func, ast.Name) else "")
            if name in COMMAND_METHODS:
                result.append((node.lineno, "command performs legacy/provider/SQL orchestration"))
    return result


def test_all_service_modules_keep_neutral_dependencies():
    for path in (ROOT / "src/stock_tracker/services").rglob("*.py"):
        assert findings(path.read_text(encoding="utf-8"), service=True) == [], str(path)


@pytest.mark.parametrize("name", ["menu_watchlist.py", "daniils_stock_method.py"])
def test_maintained_commands_delegate_infrastructure(name):
    assert findings((ROOT / name).read_text(encoding="utf-8"), service=False) == []


@pytest.mark.parametrize("source", [
    "import rich", "from config import load_configuration", "import sqlite3 as storage",
    "from stock_tracker.providers import factory as factory_alias",
    "from stock_tracker.compatibility.numeric import to_decimal", "import os",
])
def test_service_checker_rejects_controlled_boundary_violations(source):
    assert findings(source, service=True)


@pytest.mark.parametrize("source", [
    "watchlist.refresh_stocks()", "stock.get_stock_info()", "watchlist.graph_stock(symbol)",
    "from urllib.request import urlopen as fetch", "import sqlite3 as storage",
    "from stock_tracker.providers.factory import create_market_data_provider as acquire",
])
def test_command_checker_rejects_controlled_boundary_violations(source):
    assert findings(source, service=False)


def test_neutral_and_presentation_adapter_controls_are_permitted():
    assert findings("from .models import EntryUpdate\nfrom decimal import Decimal\n"
                    "from stock_tracker.providers.protocols import MarketDataProvider", service=True) == []
    assert findings("from pathlib import Path\nfrom stock_tracker.cli.composition import current_service",
                    service=False) == []
