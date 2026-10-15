"""IO-free FastAPI factory and shared-service watchlist/history adapters."""

from datetime import date
import re
from typing import Annotated

from fastapi import FastAPI, Path, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from stock_tracker.domain.errors import DomainValidationError
from stock_tracker.exceptions import StockTrackerError
from stock_tracker.services.models import HistoryView, validated_record

from .access import AccessBoundary, validate_token
from .context import Admission, ApiServices, run_data_operation
from .errors import ApiFailure, ERRORS, error_code, record_failure
from .json_response import BoundedJSONResponse, error_response
from .schemas import ErrorResponse, HealthResponse, HistoryResponse, WatchlistResponse
from .serialization import history_payload, watchlist_payload


PROTECTED_OPENAPI = {"security": [{"LocalBearer": []}]}


def error_documents():
    """Reusable typed fixed examples for later router response declarations."""
    responses = {}
    for code, (status, message) in ERRORS.items():
        response = responses.setdefault(status, {"model": ErrorResponse, "description": "Fixed safe failure.",
                                                "content": {"application/json": {"examples": {}}}})
        response["content"]["application/json"]["examples"][code] = {
            "value": {"error": {"code": code, "message": message}},
        }
    return responses


def create_app(*, token: str | None = None, services: ApiServices | None = None, dashboard: bool = False) -> FastAPI:
    """Construct an injectable app without credentials, state or provider IO.

    An absent token permits public health and opt-in static resources only;
    every API request fails auth.
    Later production configuration must require a valid operator token at launch.
    """
    validate_token(token)
    if type(dashboard) is not bool:
        raise ValueError("Dashboard configuration is invalid.")
    if services is not None and not isinstance(services, ApiServices):
        raise ValueError("Invalid API service dependencies.")
    app = FastAPI(title="Stock Tracking App local API", version="1.0.0",
                  openapi_url=None, docs_url=None, redoc_url=None,
                  redirect_slashes=False, default_response_class=BoundedJSONResponse)
    app.state.api_services = services if services is not None else ApiServices()
    app.state.api_admission = Admission()
    def access_boundary(app):
        # Starlette includes middleware keyword arguments in its repr. Capture
        # the credential privately rather than exposing it through diagnostics.
        return AccessBoundary(app, token=token, dashboard=dashboard)

    app.add_middleware(access_boundary)

    async def known_failure(request, error):
        code = error_code(error)
        record_failure(code)
        return error_response(code)

    for category in (ApiFailure, StockTrackerError, DomainValidationError, Exception):
        app.add_exception_handler(category, known_failure)

    async def invalid_input(request, error):
        return error_response("invalid_request")

    app.add_exception_handler(RequestValidationError, invalid_input)

    async def http_failure(request, error):
        code = {404: "not_found", 405: "method_not_allowed"}.get(error.status_code, "internal_error")
        response = error_response(code)
        if code == "method_not_allowed":
            response.headers["Allow"] = "GET"
        return response

    app.add_exception_handler(HTTPException, http_failure)

    @app.get("/health", response_model=HealthResponse,
             responses={**error_documents(), 200: {"content": {"application/json": {"example": {"status": "ok"}}}}},
             summary="Process liveness; no configuration, state or market access.")
    async def health():
        return {"status": "ok"}

    @app.get("/api/v1/openapi.json", responses=error_documents(), openapi_extra=PROTECTED_OPENAPI,
             summary="Authenticated static API schema; no application dependency acquisition.")
    async def schema():
        return BoundedJSONResponse(app.openapi())

    @app.get("/api/v1/watchlists/{namespace}", response_model=WatchlistResponse,
             responses={**error_documents(), 200: {"content": {"application/json": {"example": {
                 "namespace": "menu_watchlist", "name": "Watchlist", "observation": "saved",
                 "provenance": {"source": None, "observed_at": None, "retrieved_at": None, "freshness": "unknown"},
                 "entries": [],
             }}}}}, openapi_extra=PROTECTED_OPENAPI,
             summary="Saved ordered watchlist observations; freshness and currency provenance unknown.")
    async def saved_watchlist(namespace: str):
        if namespace not in ("menu_watchlist", "daniils_stock_method"):
            raise ApiFailure("not_found")

        def operation():
            acquire = app.state.api_services.watchlist
            if acquire is None:
                raise ApiFailure("internal_error")
            service = acquire(namespace)
            payload = watchlist_payload(service.view(service.load()))
            if payload["namespace"] != namespace:
                raise ApiFailure("internal_error")
            return payload

        return await run_data_operation(app, operation)

    @app.get("/api/v1/watchlists/{namespace}/entries/{ordinal}/history", response_model=HistoryResponse,
             responses={**error_documents(), 200: {"content": {"application/json": {"example": {
                 "stock": {"symbol": "AAPL", "name": None, "exchange": "NASDAQ"}, "ordinal": 0,
                 "start": "2020-01-02", "end": "2020-01-06", "price_basis": "raw",
                 "provenance": {"source": None, "observed_at": None, "retrieved_at": None,
                                "currency": None, "freshness": "unknown"},
                 "bars": [{"symbol": "AAPL", "date": "2020-01-02", "open": "100.00", "high": "120",
                           "low": "99", "close": "110.0000000000000000001", "adjusted_close": None, "volume": 0}],
             }}}}}, openapi_extra={**PROTECTED_OPENAPI, "parameters": [
                 *[{"name": name, "in": "query", "required": False,
                    "description": "Inclusive ISO calendar date. Supply exactly one start and one end, or omit both for existing UTC defaults.",
                    "schema": {"type": "string", "format": "date", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}} for name in ("start", "end")],
             ]}, summary="Raw sparse history for a freshly loaded exact stored row; unknown currency and timestamps.")
    async def stored_history(
        namespace: Annotated[str, Path(json_schema_extra={"enum": ["menu_watchlist", "daniils_stock_method"]})],
        ordinal: Annotated[str, Path(pattern=r"^[0-9]+$", description="Nonnegative zero-based request-local stored row; ASCII decimal digits only, preserving duplicates.")],
        request: Request,
    ):
        if namespace not in ("menu_watchlist", "daniils_stock_method"):
            raise ApiFailure("not_found")
        if re.fullmatch(r"[0-9]+", ordinal, re.ASCII) is None:
            raise ApiFailure("invalid_request")
        selected = int(ordinal)
        start = end = None
        try:
            query = request.scope.get("query_string", b"").decode("ascii")
            if query and any(not segment or "=" not in segment for segment in query.split("&")):
                raise ValueError()
            pairs = request.query_params.multi_items()
            if pairs:
                if len(pairs) != 2 or {key for key, value in pairs} != {"start", "end"}:
                    raise ValueError()
                values = dict(pairs)
                if any(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value, re.ASCII) is None for value in values.values()):
                    raise ValueError()
                start, end = date.fromisoformat(values["start"]), date.fromisoformat(values["end"])
        except (ValueError, UnicodeError):
            raise ApiFailure("invalid_request") from None
        services = app.state.api_services
        if not services.history_enabled:
            raise ApiFailure("history_disabled")

        def operation():
            if services.watchlist is None or services.history is None:
                raise ApiFailure("internal_error")
            record = validated_record(services.watchlist(namespace).load())
            if record.namespace != namespace:
                raise ApiFailure("internal_error")
            if selected >= len(record.entries):
                raise ApiFailure("not_found")
            stock = record.entries[selected].stock
            view = services.history.history(stock, ordinal=selected, start=start, end=end)
            if not isinstance(view, HistoryView) or view.stock is not stock:
                raise ApiFailure("internal_error")
            if start is not None and (view.start != start or view.end != end):
                raise ApiFailure("internal_error")
            return history_payload(view, ordinal=selected, services=services)

        return await run_data_operation(app, operation, history=True)

    default_openapi = app.openapi

    def documented_openapi():
        document = default_openapi()
        # FastAPI's OpenAPI model casts this integer constraint to float 0.0.
        # Restore the approved exact ordinal bound without permitting floats in
        # financial payloads or weakening the bounded JSON response encoder.
        document["components"]["schemas"]["EntryResponse"]["properties"]["ordinal"]["minimum"] = 0
        document["components"]["schemas"]["HistoryResponse"]["properties"]["ordinal"]["minimum"] = 0
        volume = document["components"]["schemas"]["BarResponse"]["properties"]["volume"]["anyOf"]
        integer = next(branch for branch in volume if branch.get("type") == "integer")
        integer["minimum"], integer["maximum"] = 0, 9223372036854775807
        document.setdefault("components", {}).setdefault("securitySchemes", {})["LocalBearer"] = {
            "type": "http", "scheme": "bearer",
            "description": "Operator-supplied local token; never a provider credential. Exactly one Authorization header.",
        }
        return document

    app.openapi = documented_openapi

    if dashboard:
        from .dashboard import register_dashboard

        register_dashboard(app)

    return app
