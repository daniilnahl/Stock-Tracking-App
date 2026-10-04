"""Offline failure, redaction and legacy entry-point regression coverage."""

import io
import logging
from pathlib import Path
import pickle
import runpy
from urllib.error import HTTPError, URLError

import pytest
from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value", [None, "", " \t\n"])
def test_missing_or_blank_key_is_rejected(value):
    from config import ConfigurationError, require_api_key

    with pytest.raises(ConfigurationError, match="Set FMP_API_KEY"):
        require_api_key(value)


def test_configuration_repr_hides_key():
    from config import load_configuration
    from unittest.mock import patch

    with patch.dict("os.environ", {"FMP_API_KEY": "synthetic-secret"}):
        configuration = load_configuration()
    assert configuration.api_key == "synthetic-secret"
    assert repr(configuration) == "Configuration()"
    assert str(configuration) == "Configuration()"


def test_dotenv_error_is_sanitized(monkeypatch, caplog):
    import dotenv
    from config import ConfigurationError, load_configuration

    def fail():
        raise OSError("synthetic-secret https://example.invalid/?" + "apikey=synthetic-secret")

    monkeypatch.setattr(dotenv, "load_dotenv", fail)
    with pytest.raises(ConfigurationError) as caught:
        load_configuration()
    assert str(caught.value) == "Unable to load local credential configuration."
    assert "synthetic-secret" not in caplog.text
    assert "https://" not in caplog.text


@pytest.mark.parametrize("script", ["menu_watchlist.py", "daniils_stock_method.py"])
@pytest.mark.parametrize("command", ["add-stock", "refresh"])
@pytest.mark.parametrize("value", [None, "", " \t\n"])
def test_network_commands_fail_before_work(script, command, value, monkeypatch, tmp_path):
    if value is not None:
        monkeypatch.setenv("FMP_API_KEY", value)
        monkeypatch.setenv("MY_API_KEY", "synthetic-legacy")
    module = runpy.run_path(str(ROOT / script), run_name="configuration_test")

    def forbidden(*args, **kwargs):
        pytest.fail("Network command reached work without a credential")

    monkeypatch.setattr(module["utility_module"], "check_ticker", forbidden)
    monkeypatch.setattr(module["current_watchlist"], "refresh_stocks", forbidden)
    result = CliRunner().invoke(module["app"], [command])
    assert result.exit_code == 1
    assert "Set FMP_API_KEY" in result.output
    assert "synthetic-legacy" not in result.output
    assert "Enter stock ticker" not in result.output
    assert not (tmp_path / module["WATCHLIST_FILE"]).exists()


@pytest.mark.parametrize("failure", ["http", "url", "unexpected", "json"])
def test_request_diagnostics_never_expose_credentials(failure, monkeypatch, caplog, capsys):
    from utils import utility_module

    url = "https://example.invalid/?" + "apikey=synthetic-secret"

    def transport(*args, **kwargs):
        if failure == "http":
            raise HTTPError(url, 401, url, None, None)
        if failure == "url":
            raise URLError(url)
        if failure == "unexpected":
            raise RuntimeError(url)
        return io.BytesIO(url.encode())

    monkeypatch.setattr(utility_module, "urlopen", transport)
    with caplog.at_level(logging.WARNING):
        assert utility_module.get_jsonparsed_data(url) is None
    captured = capsys.readouterr()
    diagnostics = captured.out + captured.err + caplog.text
    assert "synthetic-secret" not in diagnostics
    assert url not in diagnostics
    assert caplog.records
    assert all(record.exc_info is None for record in caplog.records)


def test_request_success_is_preserved(monkeypatch):
    from utils import utility_module

    monkeypatch.setattr(utility_module, "urlopen", lambda *a, **kw: io.BytesIO(b'[{"price": 10}]'))
    assert utility_module.get_jsonparsed_data("https://example.invalid/") == [{"price": 10}]


@pytest.mark.parametrize("script", ["menu_watchlist.py", "daniils_stock_method.py"])
def test_successful_add_does_not_persist_configuration(script, monkeypatch, tmp_path):
    from config import Configuration
    from stock import Stock

    monkeypatch.setenv("FMP_API_KEY", "synthetic-secret")
    module = runpy.run_path(str(ROOT / script), run_name="configuration_test")
    monkeypatch.setattr(module["utility_module"], "check_ticker", lambda *a: True)

    def profile(stock):
        stock.name = "Fictional company"
        stock.current_price = "10"

    monkeypatch.setattr(Stock, "get_stock_info", profile)
    monkeypatch.setattr(Stock, "get_price_over_time", lambda stock: None)
    result = CliRunner().invoke(module["app"], ["add-stock"], input="aapl\n2\n5\n")
    assert result.exit_code == 0, result.output
    saved = pickle.loads((tmp_path / module["WATCHLIST_FILE"]).read_bytes())
    assert saved.stocks[0].ticker_symbol == "AAPL"
    assert saved.stocks[0].API_KEY == "synthetic-secret"  # Rebound from current runtime config.
    assert "API_KEY" not in saved.stocks[0].__getstate__()
    assert b"synthetic-secret" not in (tmp_path / module["WATCHLIST_FILE"]).read_bytes()
    assert not any(isinstance(value, Configuration) for value in vars(saved).values())
    assert not any(isinstance(value, Configuration) for value in vars(saved.stocks[0]).values())
    assert "synthetic-secret" not in result.output
