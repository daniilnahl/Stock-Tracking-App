"""Outer ASGI boundary: reject unsafe requests before any application work."""

import hmac
import re

from .errors import ApiFailure, error_code, record_failure
from .json_response import error_response


TOKEN = re.compile(r"[A-Za-z0-9_-]{32,256}\Z", re.ASCII)
MAX_TARGET_BYTES = 2048
ALLOWED_HOSTS = (b"127.0.0.1:8000", b"localhost:8000")
DASHBOARD_HEADERS = (
    (b"content-security-policy", b"default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'none'"),
    (b"referrer-policy", b"no-referrer"),
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
)


def validate_token(value: str | None) -> None:
    if value is not None and (not isinstance(value, str) or TOKEN.fullmatch(value) is None):
        raise ValueError("API token configuration is invalid.")


class AccessBoundary:
    def __init__(self, app, *, token: str | None, dashboard: bool = False):
        self.app, self._token = app, token
        self._dashboard = dashboard

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
                return
            await self.app(scope, receive, send)
            return
        started = False

        async def guarded_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                message = dict(message)
                headers = [(key, value) for key, value in message.get("headers", [])
                           if key.lower() != b"cache-control"]
                message["headers"] = [*headers, (b"cache-control", b"no-store")]
                if self._dashboard:
                    message["headers"].extend(DASHBOARD_HEADERS)
            await send(message)

        try:
            headers = scope.get("headers", [])

            def values(name):
                return [value for key, value in headers if key.lower() == name]

            target = scope.get("raw_path", scope["path"].encode("utf-8"))
            query = scope.get("query_string", b"")
            if len(target) + (1 + len(query) if query else 0) > MAX_TARGET_BYTES:
                raise ApiFailure("request_too_large")
            host = values(b"host")
            if len(host) != 1 or host[0] not in ALLOWED_HOSTS:
                raise ApiFailure("host_invalid")
            origins = values(b"origin")
            if origins and (not self._dashboard or origins != [b"http://" + host[0]]):
                raise ApiFailure("origin_forbidden")
            path = scope["path"]
            if self._dashboard and (path == "/" or path.startswith("/dashboard-assets/")):
                # Refuse encoded aliases even when the ASGI server decoded them
                # into an otherwise allowlisted path. Never normalize filenames.
                if target != path.encode("ascii", errors="replace"):
                    raise ApiFailure("not_found")
            if path == "/api/v1" or path.startswith("/api/v1/"):
                authorization = values(b"authorization")
                if len(authorization) != 1 or self._token is None:
                    raise ApiFailure("unauthorized")
                scheme, separator, candidate = authorization[0].partition(b" ")
                if scheme.lower() != b"bearer" or separator != b" ":
                    raise ApiFailure("unauthorized")
                try:
                    supplied = candidate.decode("ascii")
                except UnicodeDecodeError:
                    raise ApiFailure("unauthorized") from None
                if TOKEN.fullmatch(supplied) is None or not hmac.compare_digest(supplied, self._token):
                    raise ApiFailure("unauthorized")
            # Future history handler validates the exact paired-date grammar.
            # Fixed routes and unsupported paths cannot accept hidden options.
            if query and not path.endswith("/history") and path != "/api/v1/research/upcoming-eps":
                raise ApiFailure("invalid_request")
            lengths = values(b"content-length")
            if lengths and (len(lengths) != 1 or not lengths[0] or
                            not lengths[0].isdigit() or any(char != 48 for char in lengths[0])):
                raise ApiFailure("invalid_request")
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                if message["type"] != "http.request" or message.get("body", b""):
                    raise ApiFailure("invalid_request")
                if not message.get("more_body", False):
                    break

            replay = True

            async def empty_receive():
                nonlocal replay
                if replay:
                    replay = False
                    return {"type": "http.request", "body": b"", "more_body": False}
                return await receive()

            await self.app(scope, empty_receive, guarded_send)
        except Exception as error:
            code = error_code(error)
            record_failure(code)
            if not started:
                await error_response(code)(scope, receive, guarded_send)
            # Our routes encode before sending. If an ASGI transport fails after
            # headers, no second response or raw exception diagnostic is safe.
