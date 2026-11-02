"""Translates errors to the shared JSON error format from the contract."""

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.business.models import (
    CapacityConflict,
    DomainError,
    FieldError,
    IdempotencyConflict,
    ResourceCancelled,
    ResourceNotFound,
    TemporarilyUnavailable,
    ValidationFailed,
)

logger = logging.getLogger("hotel.api")

RETRY_AFTER_SECONDS = "2"
INVALID_REQUEST_MESSAGE = "Forespørgslen er ugyldig."
TRANSPORT_MESSAGES = {
    "missing": "Feltet skal udfyldes.",
    "extra_forbidden": "Feltet er ikke tilladt.",
    "json_invalid": "Indholdet er ikke gyldig JSON.",
}
DOMAIN_ERRORS = {
    ResourceNotFound: (404, "not_found"),
    CapacityConflict: (409, "capacity_conflict"),
    ResourceCancelled: (409, "resource_cancelled"),
    IdempotencyConflict: (409, "idempotency_conflict"),
}


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or str(uuid4())


def _error_response(
    request: Request,
    status: int,
    code: str,
    message: str,
    field_errors: list[FieldError] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        headers=headers,
        content={
            "code": code,
            "message": message,
            "fieldErrors": [{"field": item.field, "message": item.message} for item in field_errors or []],
            "requestId": _request_id(request),
        },
    )


def _transport_field_error(error: dict) -> FieldError:
    location = [str(part) for part in error["loc"] if part not in ("body", "query", "path", "header")]
    # An empty form field arrives as "", which means the same as a missing one.
    is_empty = error.get("input") == ""
    return FieldError(
        field=".".join(location) or "body",
        message=TRANSPORT_MESSAGES["missing"] if is_empty else TRANSPORT_MESSAGES.get(error["type"], "Værdien er ugyldig."),
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_transport_validation(request: Request, error: RequestValidationError):
        fields = [_transport_field_error(item) for item in error.errors()]
        return _error_response(request, 400, "validation_error", INVALID_REQUEST_MESSAGE, fields)

    @app.exception_handler(ValidationFailed)
    async def handle_validation(request: Request, error: ValidationFailed):
        return _error_response(request, 400, "validation_error", error.message, error.field_errors)

    @app.exception_handler(TemporarilyUnavailable)
    async def handle_unavailable(request: Request, error: TemporarilyUnavailable):
        logger.warning("request_id=%s unavailable: %s", _request_id(request), error.__cause__ or error.message)
        return _error_response(
            request, 503, "service_unavailable", error.message, headers={"Retry-After": RETRY_AFTER_SECONDS}
        )

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, error: DomainError):
        status, code = DOMAIN_ERRORS[type(error)]
        return _error_response(request, status, code, error.message)

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, error: HTTPException):
        if error.status_code == 405:
            return _error_response(request, 405, "method_not_allowed", "Metoden understøttes ikke.")
        return _error_response(request, error.status_code, "not_found", "Adressen findes ikke.")

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, error: Exception):
        logger.error("request_id=%s unexpected error", _request_id(request), exc_info=error)
        return _error_response(request, 500, "internal_error", "Der opstod en uventet fejl.")
