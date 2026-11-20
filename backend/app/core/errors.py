from typing import Any, List, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "internal_error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[List[Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", details: Optional[List[Any]] = None):
        super().__init__(
            message=message,
            code="not_found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(AppError):
    def __init__(self, message: str = "Resource state conflict", details: Optional[List[Any]] = None):
        super().__init__(
            message=message,
            code="resource_conflict",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required", details: Optional[List[Any]] = None):
        super().__init__(
            message=message,
            code="unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(AppError):
    def __init__(self, message: str = "Permission denied", details: Optional[List[Any]] = None):
        super().__init__(
            message=message,
            code="forbidden",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed", details: Optional[List[Any]] = None):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(loc) for loc in err.get("loc", []) if loc != "body"),
            "message": err.get("msg", "Validation error"),
            "code": err.get("type", "invalid_field"),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request payload validation failed",
                "details": details,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from app.core.logging import logger

    logger.exception(f"Unhandled server error processing {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected server error occurred. Please try again later.",
                "details": [],
            }
        },
    )
