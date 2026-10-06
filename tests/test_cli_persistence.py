"""Both real CLI namespaces, lazy SQLite restoration and safe failure boundaries."""

from pathlib import Path
import pickle
import runpy
import sqlite3
import subprocess
import sys

import pytest
from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=["menu_watchlist.py", "daniils_stock_method.py"])
def cli(request, monkeypatch):
    monkeypatch.setenv("FMP_API_KEY", "synthetic-cli-storage")
    monkeypatch.setenv("COLUMNS", "300")
    module = runpy.run_path(str(ROOT / request.param), run_name="cli_storage_test")
    return module, request.param


def fresh(script):
    return runpy.run_path(str(ROOT / script), run_name="cli_storage_restart")


def holdings(name="Saved"):
    from stock import Stock
    from watch_list import Watch_list
    return Watch_list(name, [
        Stock("AAPL", None, name="Apple", exchange="NASDAQ", current_price="120",
              amount_owned="0.12345678901234567890123456789", cost_basis="100.0000000001"),
        Stock("AAPL", None, name="Other", exchange="NYSE", current_price=None,
              amount_owned="0", cost_basis="-"),
    ])


def test_import_and_help_do_not_open_sqlite_or_pickle(cli, monkeypatch):
    module, script = cli
    legacy = module["LEGACY_WATCHLIST_FILE"]
    legacy.write_bytes(b"untrusted legacy bytes")
    module["WATCHLIST_FILE"].write_bytes(b"corrupt SQLite bytes")
    def denied(*args, **kwargs):
        pytest.fail("Help attempted storage access")
    monkeypatch.setattr(sqlite3, "connect", denied)
    for name in ("load", "loads", "dump", "dumps"):
        monkeypatch.setattr(pickle, name, denied)
    monkeypatch.delenv("FMP_API_KEY")
    monkeypatch.setattr(Path, "lstat", denied)
    reloaded = fresh(script)
    assert reloaded["current_watchlist"].stocks == []
    commands = ["show-stocks", "add-stock", "refresh", "remove-stock"]
    if script == "menu_watchlist.py":
        commands.append("graph-stock")
    for args in [["--help"], *[[command, "--help"] for command in commands]]:
        result = CliRunner().invoke(reloaded["app"], args)
        assert result.exit_code == 0, result.output
        assert "Usage:" in result.output
    assert legacy.read_bytes() == b"untrusted legacy bytes"
    assert module["WATCHLIST_FILE"].read_bytes() == b"corrupt SQLite bytes"


def test_empty_display_and_load_create_no_state(cli):
    module, _ = cli
    assert module["load_watchlist"]().stocks == []
    result = CliRunner().invoke(module["app"], ["show-stocks"])
    assert result.exit_code == 0, result.output
    assert not module["WATCHLIST_FILE"].exists()
    assert not module["LEGACY_WATCHLIST_FILE"].exists()


def test_legacy_directory_entry_existence_does_not_follow_target(cli, monkeypatch):
    from stock_tracker.exceptions import LegacyStatePresentError
    module, _ = cli
    calls = []
    def entry_exists(path):
        assert path == module["LEGACY_WATCHLIST_FILE"]
        calls.append(path)
        return object()  # Simulate an occupied dangling symlink directory entry.
    monkeypatch.setattr(Path, "lstat", entry_exists)
    with pytest.raises(LegacyStatePresentError):
        module["load_watchlist"]()
    with pytest.raises(LegacyStatePresentError):
        module["save_watchlist"](holdings())
    assert calls == [module["LEGACY_WATCHLIST_FILE"]] * 2
    assert not module["WATCHLIST_FILE"].exists()


def test_legacy_existence_os_error_is_fixed_safe_failure(cli, monkeypatch):
    from stock_tracker.exceptions import PersistenceError
    module, _ = cli
    def fail(path):
        raise PermissionError("sensitive path")
    monkeypatch.setattr(Path, "lstat", fail)
    with pytest.raises(PersistenceError) as failure:
        module["load_watchlist"]()
    assert str(failure.value) == "Local storage operation failed."
    assert failure.value.__suppress_context__


def test_legacy_existence_refuses_load_save_and_commands_without_reading(cli, monkeypatch):
    from stock_tracker.exceptions import LegacyStatePresentError
    module, _ = cli
    path = module["LEGACY_WATCHLIST_FILE"]
    path.write_bytes(b"untrusted original")
    real_open = Path.open
    def guarded(path, *args, **kwargs):
        if path.suffix == ".pkl":
            pytest.fail("Legacy data opened")
        return real_open(path, *args, **kwargs)
    with monkeypatch.context() as local:
        local.setattr(Path, "open", guarded)
        local.setattr(pickle, "load", lambda *a: pytest.fail("Unpickled"))
        local.setattr(pickle, "dump", lambda *a: pytest.fail("Pickled"))
        with pytest.raises(LegacyStatePresentError):
            module["load_watchlist"]()
        with pytest.raises(LegacyStatePresentError):
            module["save_watchlist"](holdings())
        for command in ("show-stocks", "remove-stock", "add-stock", "refresh"):
            result = CliRunner().invoke(module["app"], [command], input="aapl\n")
            assert result.exit_code == 1, result.output
            assert "Preserve the original legacy file" in result.output
            assert "manual neutral-data transition" in result.output
            assert "Succesfully" not in result.output
    assert path.read_bytes() == b"untrusted original"
    assert not module["WATCHLIST_FILE"].exists()


def test_existing_namespace_is_authoritative_and_rebinds_current_key(cli, monkeypatch):
    module, script = cli
    module["save_watchlist"](holdings())
    module["LEGACY_WATCHLIST_FILE"].write_bytes(b"preserved old state")
    monkeypatch.delenv("FMP_API_KEY")
    restarted = fresh(script)
    assert restarted["current_watchlist"].stocks == []
    restored = restarted["load_watchlist"]()
    assert restored.name == "Saved" and len(restored.stocks) == 2
    assert restored.stocks[0].API_KEY is None
    assert restored.stocks[1]._position is None and restored.stocks[1].current_price is None
    before = module["WATCHLIST_FILE"].read_bytes()
    result = CliRunner().invoke(restarted["app"], ["show-stocks"], terminal_width=300)
    assert result.exit_code == 0 and "AAPL" in result.output
    assert restarted["current_watchlist"].name == "Saved"
    assert module["WATCHLIST_FILE"].read_bytes() == before
    assert module["LEGACY_WATCHLIST_FILE"].read_bytes() == b"preserved old state"
    restarted["save_watchlist"](restored)
    assert restarted["load_watchlist"]().name == "Saved"


def test_shared_path_distinct_namespaces_and_path_fixed_at_import(tmp_path, monkeypatch):
    menu, method = fresh("menu_watchlist.py"), fresh("daniils_stock_method.py")
    assert menu["WATCHLIST_FILE"] == method["WATCHLIST_FILE"] == tmp_path / "stock_tracker.sqlite3"
    menu["save_watchlist"](holdings("Menu"))
    method["save_watchlist"](holdings("Method"))
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)
    assert menu["load_watchlist"]().name == "Menu"
    assert method["load_watchlist"]().name == "Method"
    assert not (other / "stock_tracker.sqlite3").exists()


@pytest.mark.parametrize("command", ["add-stock", "refresh", "remove-stock"])
def test_failed_save_is_safe_nonzero_and_never_reports_success(cli, command, monkeypatch):
    from stock import Stock
    from stock_tracker.exceptions import PersistenceError
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    module, _ = cli
    module["current_watchlist"].stocks[:] = holdings().stocks[:1]
    module["save_watchlist"](module["current_watchlist"])
    before = module["WATCHLIST_FILE"].read_bytes()
    monkeypatch.setattr(module["utility_module"], "check_ticker", lambda *a: True)
    monkeypatch.setattr(Stock, "get_stock_info", lambda stock: None)
    monkeypatch.setattr(Stock, "get_price_over_time", lambda stock: None)
    def failing(*args):
        raise PersistenceError()
    monkeypatch.setattr(SQLiteWatchlistRepository, "save", failing)
    result = CliRunner().invoke(module["app"], [command], input="msft\n1\n100\n" if command == "add-stock" else "aapl\n")
    assert result.exit_code == 1, result.output
    assert "Local storage operation failed." in result.output
    assert "Succesfully" not in result.output and "synthetic-" not in result.output
    assert module["WATCHLIST_FILE"].read_bytes() == before


@pytest.mark.parametrize("kind", ["corrupt", "future", "malformed"])
def test_bad_database_is_refused_with_no_empty_fallback(cli, kind):
    module, script = cli
    if kind == "corrupt":
        module["WATCHLIST_FILE"].write_bytes(b"corrupt")
    else:
        module["save_watchlist"](holdings())
        with sqlite3.connect(module["WATCHLIST_FILE"]) as connection:
            if kind == "future":
                connection.execute("PRAGMA user_version=99")
            else:
                connection.execute("UPDATE watchlist_entries SET quantity='NaN'")
    before = module["WATCHLIST_FILE"].read_bytes()
    restarted = fresh(script)
    result = CliRunner().invoke(restarted["app"], ["show-stocks"])
    assert result.exit_code == 1
    assert "Local storage" in result.output
    assert str(module["WATCHLIST_FILE"]) not in result.output
    assert module["WATCHLIST_FILE"].read_bytes() == before


def test_source_cli_restart_without_pickle_or_network(tmp_path):
    for mode in ("write", "read"):
        result = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests" / "cli_persistence_probe.py"),
             str(ROOT), str(ROOT / "src"), mode],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == result.stderr == ""
