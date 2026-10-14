"""Bounded JSON encoding without float coercion or whole-response buffering."""

import json

from starlette.responses import Response

from .errors import ApiFailure, ERRORS


MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def _tokens(value):
    if value is None:
        yield b"null"
    elif type(value) is bool:
        yield b"true" if value else b"false"
    elif type(value) is str:
        yield b'"'
        # Escape small slices so a large saved string cannot force creation of a
        # second, unbounded escaped JSON string before the byte limit is checked.
        for start in range(0, len(value), 1024):
            yield json.dumps(value[start:start + 1024], ensure_ascii=True)[1:-1].encode("ascii")
        yield b'"'
    elif type(value) is int:
        yield str(value).encode("ascii")
    elif type(value) in (list, tuple):
        yield b"["
        for index, item in enumerate(value):
            if index:
                yield b","
            yield from _tokens(item)
        yield b"]"
    elif type(value) is dict:
        yield b"{"
        for index, (key, item) in enumerate(value.items()):
            if type(key) is not str:
                raise TypeError("JSON object keys must be strings.")
            if index:
                yield b","
            yield from _tokens(key)
            yield b":"
            yield from _tokens(item)
        yield b"}"
    else:
        raise TypeError("Unsupported JSON value.")


class BoundedJSONResponse(Response):
    media_type = "application/json"

    def render(self, content) -> bytes:
        result = bytearray()
        for token in _tokens(content):
            if len(result) + len(token) > MAX_RESPONSE_BYTES:
                raise ApiFailure("response_too_large")
            result.extend(token)
        return bytes(result)


def error_response(code: str) -> BoundedJSONResponse:
    status, message = ERRORS[code]
    headers = {"Cache-Control": "no-store"}
    if code == "unauthorized":
        headers["WWW-Authenticate"] = "Bearer"
    return BoundedJSONResponse({"error": {"code": code, "message": message}},
                               status_code=status, headers=headers)
