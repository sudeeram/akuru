from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class ErrorItem(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorItem


@dataclass
class DomainError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: list[dict[str, Any]] | None = None


def error_content(code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_content(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "location": [str(part) for part in issue["loc"]],
                "message": issue["msg"],
                "type": issue["type"],
            }
            for issue in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_content("validation_error", "Check the highlighted information.", details),
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        code_by_status = {
            400: "invalid_request",
            401: "authentication_required",
            403: "permission_denied",
            404: "not_found",
            409: "conflict",
            413: "request_too_large",
            429: "rate_limited",
        }
        message = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
        return JSONResponse(
            status_code=exc.status_code,
            content=error_content(code_by_status.get(exc.status_code, "request_failed"), message),
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API error for %s %s", request.method, request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=error_content("processing_error", "The server could not complete the request."),
        )
