"""Native restricted transport checks with synthetic HTTPS openers only."""

from http.client import IncompleteRead
import io
import ssl
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPSHandler

import pytest

from stock_tracker.exceptions import ProviderRequestError, ProviderResponseError
from stock_tracker.providers.finnhub_transport import FinnhubHttpTransport
from stock_tracker.providers.transport import _RejectRedirect, _TransportConnectionError, _TransportTimeout


URL = "https://finnhub.io/api/v1/calendar/earnings?symbol=TEST&from=2026-10-17&to=2026-10-31&international=false"


class Body(io.BytesIO):
    status, headers = 200, {}

    def __init__(self, value):
        super().__init__(value)
        self.read_sizes = []

    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)


@pytest.fixture
def boundary(monkeypatch):
    import stock_tracker.providers.finnhub_transport as module
    state = SimpleNamespace(calls=[], handlers=[], action=Body(b"{}"))
    state.context = ssl.create_default_context()
    def context(**kwargs):
        assert kwargs == {"cafile": "synthetic-ca-path"}
        return state.context
    def open_request(request, *, timeout):
        state.calls.append((request, timeout))
        if isinstance(state.action, BaseException):
            raise state.action
        return state.action
    def opener(*handlers):
        state.handlers.extend(handlers)
        return SimpleNamespace(open=open_request)
    monkeypatch.setattr(module.ssl, "create_default_context", context)
    monkeypatch.setattr(module.certifi, "where", lambda: "synthetic-ca-path")
    monkeypatch.setattr(module, "build_opener", opener)
    state.transport = FinnhubHttpTransport(max_response_bytes=20)
    return state


def get(boundary, **changes):
    return boundary.transport.get(**{**dict(url=URL, headers={"X-Finnhub-Token": "synthetic-transport-header"},
                                           timeout_seconds=3.0), **changes})


def test_native_tls_header_redirect_and_response_closing(boundary):
    response = get(boundary)
    assert response.status == 200 and response.body == b"{}"
    assert boundary.action.closed and boundary.action.read_sizes == [21]
    request, timeout = boundary.calls[0]
    assert request.get_method() == "GET" and request.full_url == URL
    assert request.get_header("X-finnhub-token") == "synthetic-transport-header" and timeout == 3.0
    https, = [item for item in boundary.handlers if isinstance(item, HTTPSHandler)]
    assert https._context is boundary.context
    assert https._context.check_hostname and https._context.verify_mode == ssl.CERT_REQUIRED
    redirect, = [item for item in boundary.handlers if isinstance(item, _RejectRedirect)]
    assert redirect.redirect_request(None, None, 302, None, None, "https://other") is None


@pytest.mark.parametrize("size", [20, 21, 20000])
def test_read_is_bounded_before_return(boundary, size):
    boundary.action = Body(b"x" * size)
    if size == 20:
        assert len(get(boundary).body) == 20
    else:
        with pytest.raises(ProviderResponseError):
            get(boundary)
    assert boundary.action.read_sizes == [21] and boundary.action.closed


def test_http_error_status_preserved_and_closed(boundary):
    body = Body(b"synthetic-body" * 100)
    boundary.action = HTTPError("https://synthetic-private", 429, "synthetic-private", {}, body)
    assert get(boundary).status == 429
    assert body.closed and body.read_sizes == []


@pytest.mark.parametrize("failure,expected", [
    (URLError(TimeoutError("synthetic-private")), _TransportTimeout),
    (URLError(ConnectionResetError("synthetic-private")), _TransportConnectionError),
    (ssl.SSLCertVerificationError("synthetic-private"), _TransportConnectionError),
    (IncompleteRead(b"synthetic-private"), _TransportConnectionError),
])
def test_transport_diagnostics_sanitized_without_chaining(boundary, failure, expected):
    boundary.action = failure
    with pytest.raises(expected) as caught:
        get(boundary)
    assert "synthetic-private" not in str(caught.value) and caught.value.__suppress_context__
    assert len(boundary.calls) == 1


def test_body_failure_closes_response(boundary):
    class BrokenBody(Body):
        def read(self, size=-1):
            raise IncompleteRead(b"synthetic-private")
    boundary.action = BrokenBody(b"")
    with pytest.raises(_TransportConnectionError) as caught:
        get(boundary)
    assert boundary.action.closed and caught.value.__suppress_context__


@pytest.mark.parametrize("url", [
    URL.replace("https:", "http:"), URL.replace("finnhub.io", "evil.test"),
    URL.replace("finnhub.io", "finnhub.io.evil.test"),
    URL.replace("finnhub.io", "synthetic:private@finnhub.io"),
    URL.replace("finnhub.io", "finnhub.io:444"), URL + "#synthetic-private",
    URL.replace("/calendar/earnings", "/stock/eps-estimate"),
    URL.replace("/calendar/earnings", "/calendar/earnings/"),
    URL + "&" + urlencode({"token": "synthetic-private"}), URL + "&symbol=OTHER",
    URL.replace("international=false", "international=true"),
    URL.replace("symbol=TEST", "symbol="),
    "https://finnhub.io/api/v1/calendar/earnings", None, 3,
])
def test_url_admission_before_tls_or_io(boundary, url):
    with pytest.raises(ProviderRequestError) as caught:
        get(boundary, url=url)
    assert "synthetic-private" not in str(caught.value)
    assert not boundary.calls and not boundary.handlers


@pytest.mark.parametrize("parameters", [
    {"headers": {"X-Finnhub-Token": "synthetic\nprivate"}},
    {"headers": {"Bad Header": "synthetic"}}, {"headers": {"X": 1}},
    {"headers": None}, {"timeout_seconds": 0.0}, {"timeout_seconds": True},
    {"timeout_seconds": float("nan")},
])
def test_headers_timeout_admission_before_io(boundary, parameters):
    with pytest.raises(ProviderRequestError):
        get(boundary, **parameters)
    assert not boundary.calls and not boundary.handlers


@pytest.mark.parametrize("bound", [None, True, 0, -1, 1.0])
def test_native_bound_required(bound):
    with pytest.raises(ValueError):
        FinnhubHttpTransport(max_response_bytes=bound)
