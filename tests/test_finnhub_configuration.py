"""Explicit Finnhub process configuration with synthetic credentials only."""

from datetime import date, datetime, timezone
import logging
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest

from config import ConfigurationError, load_finnhub_configuration, require_finnhub_api_key


SYNTHETIC_CREDENTIAL = "synthetic-finnhub-process-credential"


@pytest.fixture(autouse=True)
def isolated_provider_keys(monkeypatch):
    for name in ("FINNHUB_API_KEY", "FMP_API_KEY", "MY_API_KEY", "finnhub_api_key", "Finnhub_Api_Key"):
        monkeypatch.delenv(name, raising=False)


def deny_dotenv(*args, **kwargs):
    pytest.fail("Finnhub configuration attempted dotenv discovery")


def test_explicit_process_loader_without_dotenv(monkeypatch, caplog, capsys):
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", deny_dotenv)
    monkeypatch.setenv("FINNHUB_API_KEY", SYNTHETIC_CREDENTIAL)
    with caplog.at_level(logging.DEBUG):
        configuration = load_finnhub_configuration()
        assert require_finnhub_api_key(configuration.api_key) == SYNTHETIC_CREDENTIAL
    assert repr(configuration) == str(configuration) == "Configuration()"
    captured = capsys.readouterr()
    assert captured.out == captured.err == caplog.text == ""


def test_loader_reads_only_named_process_variable_when_called(monkeypatch):
    import config
    reads = []
    def getenv(name):
        reads.append(name)
        return SYNTHETIC_CREDENTIAL
    monkeypatch.setattr(config.os, "getenv", getenv)
    assert config.load_finnhub_configuration().api_key == SYNTHETIC_CREDENTIAL
    assert reads == ["FINNHUB_API_KEY"]


def test_loader_samples_environment_each_explicit_call(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", SYNTHETIC_CREDENTIAL)
    first = load_finnhub_configuration()
    monkeypatch.setenv("FINNHUB_API_KEY", "synthetic-replacement")
    second = load_finnhub_configuration()
    assert first.api_key == SYNTHETIC_CREDENTIAL
    assert second.api_key == "synthetic-replacement"


@pytest.mark.parametrize("value", [None, "", " \t\n"])
def test_missing_blank_and_no_cross_provider_fallback(monkeypatch, value):
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", deny_dotenv)
    monkeypatch.setenv("FMP_API_KEY", "synthetic-fmp")
    monkeypatch.setenv("MY_API_KEY", "synthetic-legacy")
    if value is not None:
        monkeypatch.setenv("FINNHUB_API_KEY", value)
    configuration = load_finnhub_configuration()
    assert configuration.api_key == value
    with pytest.raises(ConfigurationError, match="Set FINNHUB_API_KEY"):
        require_finnhub_api_key(configuration.api_key)


@pytest.mark.parametrize("value", [True, 1, 1.0, b"synthetic-private", [], {},
    " synthetic-private", "synthetic-private ", "synthetic\tprivate", "synthetic\nprivate",
    "synthetic\rprivate", "synthetic\x00private", "synthetic\x7fprivate", "clé", "A" + chr(0xD800)])
def test_malformed_keys_rejected_without_secret_diagnostics(value, caplog, capsys):
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ConfigurationError) as caught:
            require_finnhub_api_key(value)
    assert str(caught.value) == "Finnhub credential must be a valid header value."
    captured = capsys.readouterr()
    assert captured.out == captured.err == caplog.text == ""


@pytest.mark.parametrize("value", [SYNTHETIC_CREDENTIAL, "synthetic internal space", "synth+/_=.:!?"])
def test_valid_header_values_unchanged(value):
    assert require_finnhub_api_key(value) is value


@pytest.mark.parametrize("name", ["finnhub_api_key", "Finnhub_Api_Key"])
def test_native_process_environment_case_semantics(monkeypatch, name):
    monkeypatch.setenv(name, SYNTHETIC_CREDENTIAL)
    configuration = load_finnhub_configuration()
    assert configuration.api_key == (SYNTHETIC_CREDENTIAL if os.name == "nt" else None)


@pytest.mark.parametrize("canonical,legacy,expected", [
    ("synthetic-fmp", "synthetic-legacy", "synthetic-fmp"),
    (None, "synthetic-legacy", "synthetic-legacy"),
    ("", "synthetic-legacy", ""),
    (None, None, None),
])
def test_existing_fmp_precedence_is_independent(monkeypatch, canonical, legacy, expected):
    from config import load_configuration
    monkeypatch.setenv("FINNHUB_API_KEY", SYNTHETIC_CREDENTIAL)
    if canonical is not None:
        monkeypatch.setenv("FMP_API_KEY", canonical)
    if legacy is not None:
        monkeypatch.setenv("MY_API_KEY", legacy)
    assert load_configuration().api_key == expected
    assert load_finnhub_configuration().api_key == SYNTHETIC_CREDENTIAL


def test_explicit_configuration_adapter_injection_is_header_only(monkeypatch, caplog, capsys):
    from stock_tracker.providers.finnhub import FinnhubUpcomingEpsProvider
    from stock_tracker.providers.transport import HttpResponse
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", deny_dotenv)
    monkeypatch.setenv("FINNHUB_API_KEY", SYNTHETIC_CREDENTIAL)
    monkeypatch.setenv("FMP_API_KEY", "synthetic-distinct-fmp")
    calls = []
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return HttpResponse(200, {}, b'{"earningsCalendar":[]}')
    configuration = load_finnhub_configuration()
    provider = FinnhubUpcomingEpsProvider(
        api_key=require_finnhub_api_key(configuration.api_key),
        transport=SimpleNamespace(get=get), clock=lambda: datetime(2026, 10, 17, tzinfo=timezone.utc),
        timeout_seconds=2.0, max_response_bytes=2000, max_rows=10,
    )
    assert calls == []
    assert provider.get_upcoming_eps("TEST", start=date(2026, 10, 18), end=date(2026, 10, 31),
                                     analysis_date=date(2026, 10, 17)) == ()
    url, options = calls[0]
    assert len(calls) == 1 and options["headers"] == {"X-Finnhub-Token": SYNTHETIC_CREDENTIAL}
    assert set(parse_qs(urlsplit(url).query)) == {"symbol", "from", "to", "international"}
    assert SYNTHETIC_CREDENTIAL not in url + repr(provider) + repr(configuration)
    captured = capsys.readouterr()
    assert captured.out == captured.err == caplog.text == ""


def test_cold_configuration_import_does_not_access_environment_or_dotenv(tmp_path):
    root = Path(__file__).resolve().parents[1]
    code = '''
import os
import sys
from unittest.mock import patch
import dotenv
sys.path.insert(0, sys.argv[1])
def denied(*args, **kwargs):
    raise AssertionError("Configuration import performed credential discovery")
class DeniedEnvironment:
    __getitem__ = get = __iter__ = __contains__ = keys = items = values = denied
with patch.object(os, "environ", DeniedEnvironment()), patch.object(os, "getenv", denied), patch.object(dotenv, "load_dotenv", denied):
    import config
    assert callable(config.load_finnhub_configuration)
    assert callable(config.require_finnhub_api_key)
'''
    result = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(root)],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
