"""Injectable urllib boundary and the explicitly approved ADR-0007 policy."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from http.client import HTTPException
from math import isfinite
import re
import socket
import ssl
from types import MappingProxyType
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

import certifi

from stock_tracker.exceptions import ProviderRequestError, ProviderResponseError


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if (not isinstance(self.status, int) or isinstance(self.status, bool)
                or not 100 <= self.status <= 599
                or not isinstance(self.headers, Mapping)
                or any(not isinstance(key, str) or not isinstance(value, str)
                       for key, value in self.headers.items())
                or not isinstance(self.body, bytes)):
            raise ProviderResponseError()
        object.__setattr__(self, "headers", MappingProxyType(dict(self.headers)))


class HttpTransport(Protocol):
    def get(
        self, url: str, *, headers: Mapping[str, str], timeout_seconds: float,
    ) -> HttpResponse: ...


@dataclass(frozen=True, slots=True)
class ProviderPolicy:
    timeout_seconds: float
    max_attempts: int
    retryable_statuses: frozenset[int]
    backoff_base_seconds: float
    backoff_cap_seconds: float
    retry_budget_seconds: float
    retry_on_429: bool
    quote_cache_ttl_seconds: float
    history_cache_ttl_seconds: float
    stale_cache_fallback: bool

    def __post_init__(self) -> None:
        # Invariants validate explicit configurations; the future composition
        # factory supplies the exact approved production profile, without defaults.
        for name in ("timeout_seconds", "backoff_base_seconds", "backoff_cap_seconds",
                     "retry_budget_seconds", "quote_cache_ttl_seconds", "history_cache_ttl_seconds"):
            supplied = getattr(self, name)
            if type(supplied) is not float or not isfinite(supplied):
                raise ValueError("ProviderPolicy numeric values must be finite with valid bounds.")
            minimum_valid = supplied > 0 if name in {"timeout_seconds", "retry_budget_seconds"} else supplied >= 0
            if not minimum_valid:
                raise ValueError("ProviderPolicy numeric values must be finite with valid bounds.")
        if (type(self.max_attempts) is not int or self.max_attempts < 1
                or self.backoff_cap_seconds < self.backoff_base_seconds
                or not isinstance(self.retryable_statuses, frozenset)
                or any(type(status) is not int or status not in {408, 500, 502, 503, 504}
                       for status in self.retryable_statuses)
                or self.retry_on_429 is not False or type(self.stale_cache_fallback) is not bool):
            raise ValueError("ProviderPolicy must satisfy accepted ADR-0007 invariants.")


class _TransportTimeout(Exception):
    def __init__(self) -> None:
        super().__init__("Transport timed out.")


class _TransportConnectionError(Exception):
    def __init__(self, *, retryable: bool) -> None:
        self.retryable = retryable
        super().__init__("Transport connection failed.")


def _raise_transport_failure(reason: object) -> None:
    if isinstance(reason, TimeoutError):
        raise _TransportTimeout() from None
    retryable = isinstance(reason, ConnectionResetError) or (
        isinstance(reason, socket.gaierror) and reason.errno == socket.EAI_AGAIN
    )
    raise _TransportConnectionError(retryable=retryable) from None


class _RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class UrllibHttpTransport:
    """Construction is IO-free; TLS setup and opener creation happen on get."""

    def get(
        self, url: str, *, headers: Mapping[str, str], timeout_seconds: float,
    ) -> HttpResponse:
        try:
            parts = urlsplit(url)
            valid_url = (parts.scheme == "https" and parts.hostname == "financialmodelingprep.com"
                         and parts.username is None and parts.password is None
                         and parts.port in (None, 443) and parts.path.startswith("/stable/")
                         and not parts.fragment)
        except (TypeError, ValueError):
            raise ProviderRequestError() from None
        if (not isinstance(url, str) or not valid_url
                or not isinstance(timeout_seconds, float) or not isfinite(timeout_seconds)
                or timeout_seconds <= 0
                or not isinstance(headers, Mapping)
                or any(not isinstance(key, str) or not isinstance(value, str)
                       or re.fullmatch(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+", key) is None
                       or any(ord(char) < 32 or ord(char) >= 127 for char in key + value)
                       for key, value in headers.items())):
            raise ProviderRequestError()
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            opener = build_opener(HTTPSHandler(context=context), _RejectRedirect())
            request = Request(url, headers=dict(headers), method="GET")
            try:
                response = opener.open(request, timeout=timeout_seconds)
            except HTTPError as error:
                response = error
            try:
                return HttpResponse(response.status, dict(response.headers or {}), response.read())
            finally:
                response.close()
        except URLError as error:
            _raise_transport_failure(error.reason)
        except (OSError, HTTPException) as error:
            _raise_transport_failure(error)
