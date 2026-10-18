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
        # The installed dashboard must contain exactly the reviewed source bytes.
        for name in ("index.html", "hosting.css", "hosting.js", "stock-pixel.ttf", "LICENSE.txt"):
            packaged = "stock_tracker/api/dashboard_assets/" + name
            assert archive.read(packaged) == (ROOT / "src" / packaged).read_bytes()
    assert payload == {
        "stock.py", "watch_list.py", "menu_watchlist.py", "daniils_stock_method.py",
        "utils/utility_module.py", "config.py",
        "stock_tracker/__init__.py", "stock_tracker/domain/__init__.py",
        "stock_tracker/domain/errors.py", "stock_tracker/domain/stock.py",
        "stock_tracker/domain/position.py", "stock_tracker/domain/portfolio.py",
        "stock_tracker/domain/calculations.py",
        "stock_tracker/domain/analytics.py",
        "stock_tracker/compatibility/__init__.py", "stock_tracker/compatibility/numeric.py",
        "stock_tracker/compatibility/stock_operations.py",
        "stock_tracker/compatibility/history_operations.py",
        "stock_tracker/compatibility/watchlist_persistence.py",
        "stock_tracker/compatibility/cli_persistence.py",
        "stock_tracker/compatibility/presentation.py",
        "stock_tracker/exceptions.py", "stock_tracker/providers/__init__.py",
        "stock_tracker/providers/models.py", "stock_tracker/providers/protocols.py",
        "stock_tracker/providers/transport.py", "stock_tracker/providers/fmp.py",
        "stock_tracker/providers/eps.py", "stock_tracker/providers/finnhub.py",
        "stock_tracker/providers/finnhub_transport.py",
        "stock_tracker/providers/finnhub_factory.py",
        "stock_tracker/providers/factory.py",
        "stock_tracker/providers/history_cache.py",
        "stock_tracker/persistence/__init__.py", "stock_tracker/persistence/models.py",
        "stock_tracker/persistence/protocols.py",
        "stock_tracker/persistence/history_cache.py",
        "stock_tracker/persistence/history_protocols.py",
        "stock_tracker/persistence/transfer.py",
        "stock_tracker/persistence/sqlite_watchlists.py",
        "stock_tracker/persistence/connection.py", "stock_tracker/persistence/migrations.py",
        "stock_tracker/persistence/sqlite_portfolios.py",
        "stock_tracker/services/__init__.py", "stock_tracker/services/models.py",
        "stock_tracker/services/protocols.py", "stock_tracker/services/watchlists.py",
        "stock_tracker/services/history.py", "stock_tracker/services/history_policy.py",
        "stock_tracker/services/eps.py",
        "stock_tracker/cli/__init__.py", "stock_tracker/cli/storage.py",
        "stock_tracker/services/current_data.py", "stock_tracker/services/numeric.py",
        "stock_tracker/cli/current_data.py",
        "stock_tracker/cli/composition.py", "stock_tracker/cli/presentation.py",
        "stock_tracker/api/__init__.py", "stock_tracker/api/app.py",
        "stock_tracker/api/access.py", "stock_tracker/api/context.py",
        "stock_tracker/api/errors.py", "stock_tracker/api/json_response.py",
        "stock_tracker/api/schemas.py", "stock_tracker/api/serialization.py",
        "stock_tracker/api/configuration.py", "stock_tracker/api/composition.py",
        "stock_tracker/api/launcher.py", "stock_tracker/api/__main__.py",
        "stock_tracker/api/dashboard.py",
        "stock_tracker/api/eps_budget.py",
        "stock_tracker/api/dashboard_assets/index.html",
        "stock_tracker/api/dashboard_assets/hosting.css",
        "stock_tracker/api/dashboard_assets/hosting.js",
        "stock_tracker/api/dashboard_assets/stock-pixel.ttf",
        "stock_tracker/api/dashboard_assets/LICENSE.txt",
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

    current_service = subprocess.run(
        [sys.executable, "-I", str(ROOT / "tests/current_data_service_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert current_service.returncode == 0, current_service.stderr
    assert current_service.stdout == current_service.stderr == ""

    eps_provider = subprocess.run(
        [sys.executable, "-I", "-B", str(ROOT / "tests/finnhub_eps_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30,
    )
    assert eps_provider.returncode == 0, eps_provider.stderr
    assert eps_provider.stdout == eps_provider.stderr == ""

    eps_service = subprocess.run(
        [sys.executable, "-I", "-B", str(ROOT / "tests/upcoming_eps_service_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30,
    )
    assert eps_service.returncode == 0, eps_service.stderr
    assert eps_service.stdout == eps_service.stderr == ""

    eps_composition = subprocess.run(
        [sys.executable, "-I", "-B", str(ROOT / "tests/eps_composition_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30,
    )
    assert eps_composition.returncode == 0, eps_composition.stderr
    assert eps_composition.stdout == eps_composition.stderr == ""

    api_foundation = subprocess.run(
        [sys.executable, "-I", "-B", str(ROOT / "tests/api_foundation_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30,
    )
    assert api_foundation.returncode == 0, api_foundation.stderr
    assert api_foundation.stdout == api_foundation.stderr == ""
    assert not (tmp_path / "api-foundation-probe").exists()

    api_launcher = subprocess.run(
        [sys.executable, "-I", "-B", str(ROOT / "tests/api_launcher_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30,
    )
    assert api_launcher.returncode == 0, api_launcher.stderr
    assert api_launcher.stdout == api_launcher.stderr == ""

    dashboard_hosting = subprocess.run(
        [sys.executable, "-I", "-B", str(ROOT / "tests/dashboard_hosting_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30,
    )
    assert dashboard_hosting.returncode == 0, dashboard_hosting.stderr
    assert dashboard_hosting.stdout == dashboard_hosting.stderr == ""

    m7_directory = tmp_path / "installed-m7-exit"
    m7_directory.mkdir()
    for mode in ("write", "read", "expired"):
        m7_exit = subprocess.run(
            [sys.executable, "-I", "-B", str(ROOT / "tests/m7_exit_probe.py"), str(installed), mode],
            cwd=m7_directory, env=environment, capture_output=True, text=True, timeout=60,
        )
        assert m7_exit.returncode == 0, m7_exit.stderr
        assert m7_exit.stdout == m7_exit.stderr == ""

    m6_directory = tmp_path / "installed-m6-exit"
    m6_directory.mkdir()
    for mode in ("write", "read", "failures", "read"):
        m6 = subprocess.run(
            [sys.executable, "-I", "-B", str(ROOT / "tests/m6_exit_probe.py"), str(installed), mode],
            cwd=m6_directory, env=environment, capture_output=True, text=True, timeout=45,
        )
        assert m6.returncode == 0, m6.stderr
        assert m6.stdout == m6.stderr == ""

    service_directory = tmp_path / "installed-service"
    service_directory.mkdir()
    for mode in ("isolation", "write", "read"):
        if mode == "read":
            (service_directory / "opaque.pkl").write_bytes(b"opaque synthetic legacy; never deserialize")
            service_before = (service_directory / "service.sqlite3").read_bytes()
        service_probe = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests/watchlist_service_probe.py"), str(installed), mode],
            cwd=service_directory, env=environment, capture_output=True, text=True,
        )
        assert service_probe.returncode == 0, service_probe.stderr
        assert service_probe.stdout == service_probe.stderr == ""
        if mode == "isolation":
            assert not (service_directory / "service.sqlite3").exists()
        if mode == "read":
            assert (service_directory / "service.sqlite3").read_bytes() == service_before
            assert (service_directory / "opaque.pkl").read_bytes() == b"opaque synthetic legacy; never deserialize"

    analytics_directory = tmp_path / "installed-analytics-exit"
    analytics_directory.mkdir()
    analytics_database = analytics_directory / "holdings.sqlite3"
    analytics_original = None
    for mode in ("write", "read", "read"):
        analytics_exit = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests/analytics_exit_probe.py"),
             str(installed), str(analytics_database), mode],
            cwd=analytics_directory, env=environment, capture_output=True, text=True,
        )
        assert analytics_exit.returncode == 0, analytics_exit.stderr
        assert analytics_exit.stdout == analytics_exit.stderr == ""
        if analytics_original is None:
            analytics_original = analytics_database.read_bytes()
        assert analytics_database.read_bytes() == analytics_original

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

    for mode in ("write", "read"):
        history = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests" / "history_cache_probe.py"),
             str(installed), str(tmp_path / "installed-history.json"), mode],
            cwd=tmp_path, env=environment, capture_output=True, text=True,
        )
        assert history.returncode == 0, history.stderr
        assert history.stdout == history.stderr == ""

    composition_directory = tmp_path / "installed-history-composition"
    composition_directory.mkdir()
    for mode in ("write", "read"):
        composition = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests/history_integration_probe.py"), str(installed), mode],
            cwd=composition_directory, env=environment, capture_output=True, text=True,
        )
        assert composition.returncode == 0, composition.stderr
        assert composition.stdout == composition.stderr == ""

    history_exit_directory = tmp_path / "installed-history-exit"
    history_exit_directory.mkdir()
    for mode in ("write", "read", "expired"):
        history_exit = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests/history_exit_probe.py"), str(installed), mode],
            cwd=history_exit_directory, env=environment, capture_output=True, text=True,
        )
        assert history_exit.returncode == 0, history_exit.stderr
        assert history_exit.stdout == history_exit.stderr == ""
    assert (history_exit_directory / "watchlist.pkl").read_bytes() == b"opaque synthetic legacy; do not deserialize"

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
    from stock import Stock as LegacyStock
    from watch_list import Watch_list
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.compatibility.watchlist_persistence import watchlist_to_record, record_to_watchlist
    repo = SQLiteWatchlistRepository(path)
    original = Watch_list('Installed offline', [LegacyStock('ABC', None, amount_owned='0.2500',
                          cost_basis='100.0000', current_price='120.0000')])
    repo.save(watchlist_to_record(original, 'menu_watchlist'))
    fresh = SQLiteWatchlistRepository(path)
    restored = record_to_watchlist(fresh.get('menu_watchlist'), None)
    assert restored.stocks[0].amount_owned == '0.2500'
    assert restored.stocks[0].total_return == '20.0'
    assert fresh.get('daniils_stock_method') is None
    from stock_tracker.persistence.transfer import import_neutral_state, backup_database, restore_database
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    import json
    neutral = path.with_suffix('.json')
    neutral.write_text(json.dumps({'format': 'stock-tracker-neutral', 'version': 1,
        'portfolios': [{'id': '9', 'name': 'Transferred', 'positions': []}], 'watchlists': []}),
        encoding='utf-8')
    import_neutral_state(neutral, path)
    backup = path.with_name('installed-backup.sqlite3')
    restored_path = path.with_name('installed-restored.sqlite3')
    backup_database(path, backup)
    restore_database(backup, restored_path)
    assert SQLitePortfolioRepository(restored_path).get(9).name == 'Transferred'
    assert SQLiteWatchlistRepository(restored_path).get('menu_watchlist').name == 'Installed offline'
    for name in ('stock_tracker.persistence.transfer', 'stock_tracker.persistence.migrations', 'stock_tracker.persistence.connection',
                 'stock_tracker.persistence.sqlite_watchlists',
                 'stock_tracker.compatibility.watchlist_persistence'):
        assert Path(sys.modules[name].__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
"""
    migration = subprocess.run(
        [sys.executable, "-I", "-c", migration_code, str(installed),
         str(tmp_path / "installed-migration.sqlite3")],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert migration.returncode == 0, migration.stderr
    assert migration.stdout == migration.stderr == ""

    for mode in ("write", "read"):
        portfolios = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests" / "portfolio_repository_probe.py"),
             str(installed), str(tmp_path / "installed-portfolios.sqlite3"), mode],
            cwd=tmp_path, env=environment, capture_output=True, text=True,
        )
        assert portfolios.returncode == 0, portfolios.stderr
        assert portfolios.stdout == portfolios.stderr == ""

    cli_directory = tmp_path / "installed-cli"
    cli_directory.mkdir()
    for mode in ("write", "read"):
        cli = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests" / "cli_persistence_probe.py"),
             str(installed), str(installed), mode],
            cwd=cli_directory, env=environment, capture_output=True, text=True,
        )
        assert cli.returncode == 0, cli.stderr
        assert cli.stdout == cli.stderr == ""

    exit_original, exit_restored = tmp_path / "exit-original", tmp_path / "exit-restored"
    exit_original.mkdir()
    exit_restored.mkdir()
    for directory in (exit_original, exit_restored):
        for name in ("watchlist.pkl", "daniils_stock_methodd.pkl"):
            (directory / name).write_bytes(b"opaque installed legacy fixture")
    for mode, directory in (("prepare", exit_original), ("verify", exit_original),
                            ("copy", exit_original), ("verify", exit_restored)):
        audit = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests" / "persistence_exit_probe.py"),
             str(installed), str(installed), mode, str(exit_restored)],
            cwd=directory, env=environment, capture_output=True, text=True,
        )
        assert audit.returncode == 0, audit.stderr
        assert audit.stdout == audit.stderr == ""
    for directory in (exit_original, exit_restored):
        for name in ("watchlist.pkl", "daniils_stock_methodd.pkl"):
            assert (directory / name).read_bytes() == b"opaque installed legacy fixture"

    provider = subprocess.run(
        [sys.executable, '-I', str(ROOT / 'tests' / 'provider_integration_probe.py'), str(installed)],
        cwd=tmp_path, env=dict(environment, MPLCONFIGDIR=str(tmp_path / 'provider-matplotlib'), MPLBACKEND='Agg'),
        capture_output=True, text=True,
    )
    assert provider.returncode == 0, provider.stderr
    assert provider.stdout == provider.stderr == ''

    # -I and an empty cwd keep the checkout out of imports. The built wheel,
    # rather than source files, supplies the modules under verification.
    history_service = subprocess.run(
        [sys.executable, "-I", str(ROOT / "tests/history_service_probe.py"), str(installed)],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert history_service.returncode == 0, history_service.stderr
    assert history_service.stdout == history_service.stderr == ""
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
import config
def denied_dotenv(*args, **kwargs):
    raise AssertionError('Finnhub loader attempted dotenv discovery')
with patch.object(config.dotenv, 'load_dotenv', denied_dotenv), patch.object(config.os, 'getenv', return_value='synthetic-installed-finnhub') as getenv:
    finnhub_configuration = config.load_finnhub_configuration()
    assert config.require_finnhub_api_key(finnhub_configuration.api_key) == 'synthetic-installed-finnhub'
    assert repr(finnhub_configuration) == 'Configuration()'
    getenv.assert_called_once_with('FINNHUB_API_KEY')

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
