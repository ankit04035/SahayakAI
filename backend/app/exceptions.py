"""
Application Exceptions and Centralized Error Handlers.
Defines custom exception classes and registers global FastAPI exception handlers.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("sahayakai.exceptions")


class AppException(Exception):
    """Base application exception with status code and structured metadata."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class DatabaseConnectionError(AppException):
    """Raised when database connectivity fails."""

    def __init__(self, message: str = "Database connection unavailable", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_ERROR",
            details=details,
        )


class ConfigurationError(AppException):
    """Raised when application configuration is invalid or missing."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CONFIGURATION_ERROR",
            details=details,
        )


def create_error_response(
    status_code: int,
    message: str,
    error_code: str,
    details: Optional[Any] = None,
) -> JSONResponse:
    """Format consistent error response payload."""
    payload: Dict[str, Any] = {
        "status": "error",
        "error_code": error_code,
        "message": message,
        "details": details,
    }
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application instance."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "AppException on %s %s: [%s] %s",
            request.method,
            request.url.path,
            exc.error_code,
            exc.message,
        )
        return create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.info(
            "HTTPException on %s %s: [%d] %s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.detail,
        )
        return create_error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            details=None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.info("ValidationError on %s %s", request.method, request.url.path)
        formatted_errors = [
            {"loc": list(err.get("loc", [])), "msg": err.get("msg", ""), "type": err.get("type", "")}
            for err in exc.errors()
        ]
        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            error_code="VALIDATION_ERROR",
            details=formatted_errors,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled server exception on %s %s: %s",
            request.method,
            request.url.path,
            str(exc),
            exc_info=True,
        )
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected internal server error occurred.",
            error_code="INTERNAL_SERVER_ERROR",
            details=None,
        )
