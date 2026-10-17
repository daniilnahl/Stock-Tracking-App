"""Restricted, bounded Finnhub calendar transport; no retry or configuration IO."""

from collections.abc import Mapping
from http.client import HTTPException
from math import isfinite
import re
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPSHandler, Request, build_opener

import certifi

from stock_tracker.exceptions import ProviderRequestError, ProviderResponseError
from .transport import HttpResponse, _RejectRedirect, _raise_transport_failure


class FinnhubHttpTransport:
    """Only the accepted HTTPS calendar route, with bounded native reads."""

    def __init__(self, *, max_response_bytes: int) -> None:
        if type(max_response_bytes) is not int or max_response_bytes < 1:
            raise ValueError("A positive response byte limit is required.")
        self._max_response_bytes = max_response_bytes

    def get(
        self, url: str, *, headers: Mapping[str, str], timeout_seconds: float,
    ) -> HttpResponse:
        try:
            parts = urlsplit(url)
            parameters = parse_qs(parts.query, keep_blank_values=True, strict_parsing=True)
            valid_url = (
                parts.scheme == "https" and parts.hostname == "finnhub.io"
                and parts.username is None and parts.password is None
                and parts.port in (None, 443) and parts.path == "/api/v1/calendar/earnings"
                and not parts.fragment
                and set(parameters) == {"symbol", "from", "to", "international"}
                and all(len(values) == 1 and values[0] for values in parameters.values())
                and parameters["international"] == ["false"]
            )
        except (TypeError, ValueError, AttributeError):
            raise ProviderRequestError() from None
        if (not isinstance(url, str) or not valid_url
                or type(timeout_seconds) is not float or not isfinite(timeout_seconds)
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
                if response.status != 200:
                    # Status classifies failure; discard unneeded, potentially
                    # oversized error bodies without exposing their contents.
                    return HttpResponse(response.status, {}, b"")
                body = response.read(self._max_response_bytes + 1)
                if len(body) > self._max_response_bytes:
                    raise ProviderResponseError()
                return HttpResponse(response.status, dict(response.headers or {}), body)
            finally:
                response.close()
        except URLError as error:
            _raise_transport_failure(error.reason)
        except (OSError, HTTPException) as error:
            _raise_transport_failure(error)
