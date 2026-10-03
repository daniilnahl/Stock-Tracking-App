"""Offline credential loading through real application modules and dotenv."""

import runpy
from pathlib import Path

import pytest
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ("menu_watchlist.py", "daniils_stock_method.py", "test.py")


@pytest.fixture(params=SCRIPTS)
def load_key(request, tmp_path, monkeypatch):
    """Use the shared isolation harness and real parsing of a temporary .env."""
    import dotenv
    from dotenv.main import load_dotenv

    def load(environment, dotenv_text=""):
        env_file = tmp_path / ".env"
        if dotenv_text is not None:
            env_file.write_text(dotenv_text, encoding="utf-8")
        monkeypatch.setattr(dotenv, "load_dotenv", lambda: load_dotenv(env_file))
        for name, value in environment.items():
            monkeypatch.setenv(name, value)
        module = runpy.run_path(str(ROOT / request.param), run_name="configuration_test")
        if request.param == "test.py":
            from stock import Stock

            captured = []

            def capture_key(stock):
                captured.append(stock.API_KEY)

            # Construct a real Stock; replace only its provider operation.
            # Default socket guards remain active throughout the test.
            monkeypatch.setattr(Stock, "get_stock_info", capture_key)
            module["main"]()
            return captured[0]
        assert module["current_watchlist"].stocks == []
        assert not (tmp_path / module["WATCHLIST_FILE"]).exists()
        return module["API_KEY"]

    return load


def test_canonical_process_environment_is_loaded_by_every_script(load_key):
    assert load_key({"FMP_API_KEY": "synthetic-canonical"}) == "synthetic-canonical"


def test_canonical_name_wins_over_legacy_name(load_key):
    assert load_key({
        "FMP_API_KEY": "synthetic-canonical", "MY_API_KEY": "synthetic-legacy",
    }) == "synthetic-canonical"


def test_canonical_dotenv_is_loaded_by_every_script(load_key):
    assert load_key({}, "FMP_API_KEY=synthetic-file\n") == "synthetic-file"


def test_process_environment_overrides_same_name_in_dotenv(load_key):
    assert load_key({"FMP_API_KEY": "synthetic-process"},
                    "FMP_API_KEY=synthetic-file\n") == "synthetic-process"


def test_canonical_dotenv_wins_over_legacy_process_variable(load_key):
    assert load_key({"MY_API_KEY": "synthetic-legacy"},
                    "FMP_API_KEY=synthetic-file\n") == "synthetic-file"


@pytest.mark.parametrize("from_file", [False, True])
def test_legacy_fallback_is_preserved_when_canonical_name_is_absent(load_key, from_file):
    if from_file:
        assert load_key({}, "MY_API_KEY=synthetic-file\n") == "synthetic-file"
    else:
        assert load_key({"MY_API_KEY": "synthetic-legacy"}) == "synthetic-legacy"


def test_environment_loading_does_not_require_dotenv_file(load_key):
    assert load_key({"FMP_API_KEY": "synthetic-canonical"}, None) == "synthetic-canonical"


@pytest.mark.parametrize("environment", [
    {}, {"FMP_API_KEY": "", "MY_API_KEY": "synthetic-legacy"},
    {"FMP_API_KEY": " \t", "MY_API_KEY": "synthetic-legacy"},
], ids=["missing", "empty-canonical", "blank-canonical"])
def test_missing_and_blank_keys_allow_cli_import_but_reject_scratch_requests(load_key, request, environment):
    if request.node.callspec.params["load_key"] == "test.py":
        with pytest.raises(SystemExit, match="Set FMP_API_KEY"):
            load_key(environment)
    else:
        assert load_key(environment) == environment.get("FMP_API_KEY")


@pytest.mark.parametrize("script", SCRIPTS[:2])
def test_cli_passes_canonical_key_to_ticker_validation(script, monkeypatch):
    monkeypatch.setenv("FMP_API_KEY", "synthetic-canonical")
    monkeypatch.setenv("MY_API_KEY", "synthetic-legacy")
    module = runpy.run_path(str(ROOT / script), run_name="configuration_test")
    calls = []

    def check_ticker(ticker, api_key):
        calls.append((ticker, api_key))
        return False

    monkeypatch.setattr(module["utility_module"], "check_ticker", check_ticker)
    result = CliRunner().invoke(module["app"], ["add-stock"], input="aapl\n")
    assert result.exit_code == 0, result.output
    assert "Invalid ticker. Try again." in result.output
    assert calls == [("AAPL", "synthetic-canonical")]
