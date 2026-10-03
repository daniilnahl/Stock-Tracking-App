"""Default offline transport and filesystem boundaries for normal tests."""

import socket
import urllib.request

import pytest


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    """Keep legacy cwd-relative state and import-time configuration temporary."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MY_API_KEY", raising=False)
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    monkeypatch.setenv("MPLBACKEND", "Agg")
    # dotenv otherwise searches from the CLI source file into the real checkout.
    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    """Block urllib and socket transports, including imported urllib aliases."""
    def denied(*args, **kwargs):
        pytest.fail("Network access denied in automated tests", pytrace=False)

    monkeypatch.setattr(urllib.request, "urlopen", denied)
    monkeypatch.setattr(urllib.request.OpenerDirector, "open", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket.socket, "sendto", denied)
    # Patch a pre-existing alias if another test already imported the utility.
    import sys

    utility = sys.modules.get("utils.utility_module")
    if utility is not None:
        monkeypatch.setattr(utility, "urlopen", denied)
