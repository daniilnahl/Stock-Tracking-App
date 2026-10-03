"""Offline wheel-discovery and pinned-development-installation smoke checks."""

import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys
import tomllib
import zipfile

from packaging.requirements import Requirement


ROOT = Path(__file__).resolve().parents[1]


def test_development_installation_matches_all_dependency_pins():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = config["project"]
    pins = project["dependencies"] + project["optional-dependencies"]["dev"]
    pins += config["build-system"]["requires"]
    for pin in pins:
        requirement = Requirement(pin)
        assert len(requirement.specifier) == 1
        specifier = next(iter(requirement.specifier))
        assert specifier.operator == "=="
        assert "*" not in specifier.version
        assert importlib.metadata.version(requirement.name) == specifier.version


def test_wheel_contains_only_runtime_modules_and_safe_imports(tmp_path):
    environment = dict(os.environ, PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1")
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", str(ROOT), "--no-deps",
         "--no-build-isolation", "--wheel-dir", str(tmp_path)],
        env=environment, check=True, capture_output=True, text=True,
    )
    wheel, = tmp_path.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        payload = {name for name in archive.namelist() if ".dist-info/" not in name}
    assert payload == {
        "stock.py", "watch_list.py", "menu_watchlist.py", "daniils_stock_method.py",
        "utils/utility_module.py", "config.py",
        "stock_tracker/__init__.py", "stock_tracker/domain/__init__.py",
        "stock_tracker/domain/errors.py", "stock_tracker/domain/stock.py",
    }

    installed = tmp_path / "installed"
    subprocess.run(
        [sys.executable, "-m", "pip", "install", str(wheel), "--no-deps",
         "--no-compile", "--target", str(installed)],
        env=environment, check=True, capture_output=True, text=True,
    )

    # -I and an empty cwd keep the checkout out of imports. The built wheel,
    # rather than source files, supplies the modules under verification.
    code = """
import socket
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, sys.argv[1])
with patch.object(socket.socket, 'connect', side_effect=AssertionError('Network denied')):
    import utils.utility_module as utility
    with patch.object(utility, 'urlopen', side_effect=AssertionError('Provider denied')):
        import stock
assert stock.__file__.startswith(sys.argv[1])
assert utility.__file__.startswith(sys.argv[1])

# Installed domain must work even when legacy/provider/UI modules are unavailable.
blocked = {name: None for name in (
    'stock', 'config', 'watch_list', 'menu_watchlist', 'daniils_stock_method',
    'utils', 'utils.utility_module', 'dotenv', 'rich', 'typer', 'matplotlib',
    'urllib', 'socket', 'sqlite3',
)}
with patch.dict(sys.modules, blocked):
    import stock_tracker
    import stock_tracker.domain
    from stock_tracker.domain import Stock, DomainValidationError
    first = Stock('AAPL', exchange='NASDAQ')
    assert first == Stock('AAPL', 'Apple', 'NASDAQ')
    assert first != Stock('AAPL', exchange='NYSE')
    assert Stock('AAPL') != Stock('AAPL')
    assert issubclass(DomainValidationError, ValueError)
    for name in ('stock_tracker', 'stock_tracker.domain', Stock.__module__,
                 DomainValidationError.__module__):
        assert Path(sys.modules[name].__file__).resolve().is_relative_to(
            Path(sys.argv[1]).resolve())
"""
    subprocess.run(
        [sys.executable, "-I", "-c", code, str(installed)], cwd=tmp_path,
        env=dict(environment, MPLCONFIGDIR=str(tmp_path / "matplotlib"), MPLBACKEND="Agg"),
        check=True, capture_output=True, text=True,
    )
