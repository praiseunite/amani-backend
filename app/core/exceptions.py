"""
Custom exception handlers for better error handling and security.
"""
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class BadRequestError(APIError):
    """Bad request error (400)."""
    
    def __init__(self, message: str = "Bad request", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            details=details
        )


class UnauthorizedError(APIError):
    """Unauthorized error (401)."""
    
    def __init__(self, message: str = "Unauthorized", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            details=details
        )


class ForbiddenError(APIError):
    """Forbidden error (403)."""
    
    def __init__(self, message: str = "Forbidden", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            details=details
        )


class NotFoundError(APIError):
    """Not found error (404)."""
    
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details
        )


class ConflictError(APIError):
    """Conflict error (409)."""
    
    def __init__(self, message: str = "Resource conflict", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details
        )


class ValidationErrorException(APIError):
    """Validation error (422)."""
    
    def __init__(self, message: str = "Validation error", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class RateLimitError(APIError):
    """Rate limit exceeded error (429)."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error (503)."""
    
    def __init__(self, message: str = "Service unavailable", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details=details
        )


def create_error_response(
    status_code: int,
    message: str,
    error_code: str = None,
    details: dict = None,
    path: str = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Application-specific error code
        details: Additional error details
        path: Request path where error occurred
        
    Returns:
        JSONResponse with error details
    """
    error_response = {
        "error": {
            "code": error_code or "ERROR",
            "message": message,
            "status": status_code
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if path:
        error_response["error"]["path"] = path
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    Handler for custom API errors.
    
    Args:
        request: Request object
        exc: APIError exception
        
    Returns:
        JSONResponse with error details
    """
    logger.error(
        f"API Error: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "error_message": exc.message,
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method,
            "details": exc.details
        }
    )
    
    return create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        path=str(request.url.path)
    )


async def validation_error_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handler for Pydantic validation errors.
    
    Args:
        request: Request object
        exc: Validation error exception
        
    Returns:
        JSONResponse with validation error details
    """
    errors = []
    
    # Extract validation errors
    for error in exc.errors():
        error_detail = {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        }
        errors.append(error_detail)
    
    logger.warning(
        "Validation error",
        extra={
            "path": str(request.url),
            "method": request.method,
            "errors": errors
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Input validation failed",
        error_code="VALIDATION_ERROR",
        details={"errors": errors},
        path=str(request.url.path)
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handler for HTTP exceptions.
    
    Args:
        request: Request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with error details
    """
    logger.warning(
        f"HTTP Exception: {exc.status_code}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        error_code=f"HTTP_{exc.status_code}",
        path=str(request.url.path)
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handler for SQLAlchemy database errors.
    
    Args:
        request: Request object
        exc: SQLAlchemy exception
        
    Returns:
        JSONResponse with error details
    """
    # Log detailed error for debugging
    logger.error(
        "Database error",
        extra={
            "error_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method
        },
        exc_info=True
    )
    
    # Check for specific error types
    if isinstance(exc, IntegrityError):
        message = "Database constraint violation. The operation violates data integrity rules."
        error_code = "INTEGRITY_ERROR"
        status_code = status.HTTP_409_CONFLICT
    else:
        message = "A database error occurred. Please try again later."
        error_code = "DATABASE_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return create_error_response(
        status_code=status_code,
        message=message,
        error_code=error_code,
        path=str(request.url.path)
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handler for unhandled exceptions.
    
    Args:
        request: Request object
        exc: Exception
        
    Returns:
        JSONResponse with generic error message
    """
    # Log full exception details for debugging
    logger.exception(
        "Unhandled exception",
        extra={
            "error_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    # Return generic error message to avoid leaking sensitive information
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please try again later.",
        error_code="INTERNAL_ERROR",
        path=str(request.url.path)
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
