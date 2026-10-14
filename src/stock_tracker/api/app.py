"""IO-free FastAPI factory; data routes and production launch are later issues."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from stock_tracker.domain.errors import DomainValidationError
from stock_tracker.exceptions import StockTrackerError

from .access import AccessBoundary, validate_token
from .context import Admission, ApiServices
from .errors import ApiFailure, ERRORS, error_code, record_failure
from .json_response import BoundedJSONResponse, error_response
from .schemas import ErrorResponse, HealthResponse


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


def create_app(*, token: str | None = None, services: ApiServices | None = None) -> FastAPI:
    """Construct an injectable app without credentials, state or provider IO.

    An absent token permits only public health; every API request fails auth.
    Later production configuration must require a valid operator token at launch.
    """
    validate_token(token)
    if services is not None and not isinstance(services, ApiServices):
        raise ValueError("Invalid API service dependencies.")
    app = FastAPI(title="Stock Tracking App local API", version="1.0.0",
                  openapi_url=None, docs_url=None, redoc_url=None,
                  redirect_slashes=False, default_response_class=BoundedJSONResponse)
    app.state.api_services = services if services is not None else ApiServices()
    app.state.api_admission = Admission()
    app.add_middleware(AccessBoundary, token=token)

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

    default_openapi = app.openapi

    def documented_openapi():
        document = default_openapi()
        document.setdefault("components", {}).setdefault("securitySchemes", {})["LocalBearer"] = {
            "type": "http", "scheme": "bearer",
            "description": "Operator-supplied local token; never a provider credential. Exactly one Authorization header.",
        }
        return document

    app.openapi = documented_openapi

    return app
