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
        "stock_tracker/domain/position.py", "stock_tracker/domain/portfolio.py",
        "stock_tracker/domain/calculations.py",
        "stock_tracker/compatibility/__init__.py", "stock_tracker/compatibility/numeric.py",
        "stock_tracker/compatibility/stock_operations.py",
        "stock_tracker/compatibility/presentation.py",
        "stock_tracker/exceptions.py", "stock_tracker/providers/__init__.py",
        "stock_tracker/providers/models.py", "stock_tracker/providers/protocols.py",
        "stock_tracker/providers/transport.py", "stock_tracker/providers/fmp.py",
        "stock_tracker/providers/factory.py",
        "stock_tracker/persistence/__init__.py", "stock_tracker/persistence/models.py",
        "stock_tracker/persistence/protocols.py",
        "stock_tracker/persistence/connection.py", "stock_tracker/persistence/migrations.py",
    }

    installed = tmp_path / "installed"
    subprocess.run(
        [sys.executable, "-m", "pip", "install", str(wheel), "--no-deps",
         "--no-compile", "--target", str(installed)],
        env=environment, check=True, capture_output=True, text=True,
    )

    # Domain-only process runs first; legacy imports cannot prime its dependencies.
    isolated = subprocess.run(
        [sys.executable, "-I", str(ROOT / "tests" / "domain_isolation_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert isolated.returncode == 0, isolated.stderr
    assert isolated.stdout == isolated.stderr == ""
    assert not (tmp_path / "domain-probe").exists()

    contracts = subprocess.run(
        [sys.executable, "-I", str(ROOT / "tests" / "provider_contract_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert contracts.returncode == 0, contracts.stderr
    assert contracts.stdout == contracts.stderr == ""

    persistence = subprocess.run(
        [sys.executable, "-I", str(ROOT / "tests" / "persistence_contract_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert persistence.returncode == 0, persistence.stderr
    assert persistence.stdout == persistence.stderr == ""

    migration_code = """
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import socket
import urllib.request
sys.path.insert(0, sys.argv[1])
def denied(*args, **kwargs):
    raise AssertionError('Network denied')
with ExitStack() as guards:
    for target, attribute in (
        (urllib.request, 'urlopen'), (urllib.request.OpenerDirector, 'open'),
        (socket, 'getaddrinfo'), (socket, 'create_connection'),
        (socket.socket, 'connect'), (socket.socket, 'connect_ex'), (socket.socket, 'sendto'),
    ):
        guards.enter_context(patch.object(target, attribute, denied))
    from stock_tracker.persistence.migrations import migrate_database, validate_schema
    from stock_tracker.persistence.connection import database_connection, transaction
    path = Path(sys.argv[2])
    assert not path.exists()
    migrate_database(path)
    migrate_database(path)
    with database_connection(path) as connection:
        with transaction(connection):
            validate_schema(connection)
            assert connection.execute('PRAGMA foreign_keys').fetchone() == (1,)
            assert connection.execute('PRAGMA user_version').fetchone() == (1,)
    for name in ('stock_tracker.persistence.migrations', 'stock_tracker.persistence.connection'):
        assert Path(sys.modules[name].__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
"""
    migration = subprocess.run(
        [sys.executable, "-I", "-c", migration_code, str(installed),
         str(tmp_path / "installed-migration.sqlite3")],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert migration.returncode == 0, migration.stderr
    assert migration.stdout == migration.stderr == ""

    provider = subprocess.run(
        [sys.executable, '-I', str(ROOT / 'tests' / 'provider_integration_probe.py'), str(installed)],
        cwd=tmp_path, env=dict(environment, MPLCONFIGDIR=str(tmp_path / 'provider-matplotlib'), MPLBACKEND='Agg'),
        capture_output=True, text=True,
    )
    assert provider.returncode == 0, provider.stderr
    assert provider.stdout == provider.stderr == ''

    # -I and an empty cwd keep the checkout out of imports. The built wheel,
    # rather than source files, supplies the modules under verification.
    code = """
import socket
import sys
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, sys.argv[1])
# Installed domain must work even when legacy/provider/UI modules are unavailable.
blocked = {name: None for name in (
    'stock', 'config', 'watch_list', 'menu_watchlist', 'daniils_stock_method',
    'utils', 'utils.utility_module', 'dotenv', 'rich', 'typer', 'matplotlib',
    'urllib', 'socket', 'sqlite3', 'stock_tracker.providers', 'stock_tracker.exceptions',
)}
with patch.dict(sys.modules, blocked):
    import stock_tracker
    import stock_tracker.domain
    from stock_tracker.domain import (Stock, Position, Portfolio, DomainValidationError,
                                      PositionSnapshot, position_snapshot)
    first = Stock('AAPL', exchange='NASDAQ')
    assert first == Stock('AAPL', 'Apple', 'NASDAQ')
    assert first != Stock('AAPL', exchange='NYSE')
    assert Stock('AAPL') != Stock('AAPL')
    position = Position(first, Decimal('0.25'), Decimal('100.123456'))
    assert position.with_owned_data(Decimal('1'), Decimal('2')).stock is first
    assert position.quantity == Decimal('0.25')
    supplied = [position, position]
    portfolio = Portfolio(None, 'Example', supplied)
    assert portfolio.positions == supplied and portfolio.positions is not supplied
    supplied.clear()
    assert portfolio.positions == [position, position]
    snapshot = position_snapshot(position, Decimal('125.154320'))
    assert isinstance(snapshot, PositionSnapshot)
    assert snapshot.cost_basis == Decimal('25.030864')
    assert snapshot.market_value == Decimal('31.288580')
    assert snapshot.unrealized_pnl == Decimal('6.257716')
    assert snapshot.unrealized_return == Decimal('0.25')
    assert position_snapshot(position, None).market_value is None
    assert issubclass(DomainValidationError, ValueError)
    for name in ('stock_tracker', 'stock_tracker.domain', Stock.__module__,
                 Position.__module__, Portfolio.__module__, DomainValidationError.__module__,
                 PositionSnapshot.__module__, position_snapshot.__module__):
        assert Path(sys.modules[name].__file__).resolve().is_relative_to(
            Path(sys.argv[1]).resolve())

# Preserve installed legacy module checks after guarded fresh domain imports.
import stock_tracker.providers.transport as provider_transport
import stock_tracker.providers.fmp as provider_fmp
import stock_tracker.providers.factory as provider_factory
for module in (provider_transport, provider_fmp, provider_factory):
    assert Path(module.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
with patch.object(provider_transport.ssl, 'create_default_context', side_effect=AssertionError('TLS IO denied')):
    provider_transport.UrllibHttpTransport()

with patch.object(socket.socket, 'connect', side_effect=AssertionError('Network denied')):
    import utils.utility_module as utility
    with patch.object(utility, 'urlopen', side_effect=AssertionError('Provider denied')):
        import stock
        legacy = stock.Stock('AAPL', None, current_price='120', amount_owned='10', cost_basis='100')
        assert legacy.total_return == '20.0'
        assert legacy._position.quantity == Decimal('10')
        assert 'API_KEY' not in legacy.__getstate__()
        assert '_runtime_key' not in legacy.__getstate__()
for name in ('stock', 'utils.utility_module', 'stock_tracker.compatibility.numeric',
             'stock_tracker.compatibility.presentation', 'stock_tracker.compatibility.stock_operations'):
    assert Path(sys.modules[name].__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
"""
    subprocess.run(
        [sys.executable, "-I", "-c", code, str(installed)], cwd=tmp_path,
        env=dict(environment, MPLCONFIGDIR=str(tmp_path / "matplotlib"), MPLBACKEND="Agg"),
        check=True, capture_output=True, text=True,
    )
