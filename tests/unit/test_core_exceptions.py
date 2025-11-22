"""
Comprehensive unit tests for app.core.exceptions module.
Tests custom exception classes and error response formatting.
"""

import pytest
from fastapi import status
from app.core.exceptions import (
    APIError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    ValidationErrorException,
    RateLimitError,
    ServiceUnavailableError,
    create_error_response,
)


class TestAPIError:
    """Test suite for base APIError class."""

    def test_api_error_initialization(self):
        """Test APIError initialization with all parameters."""
        error = APIError(
            message="Test error",
            status_code=500,
            error_code="TEST_ERROR",
            details={"key": "value"},
        )
        
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}

    def test_api_error_default_status_code(self):
        """Test APIError default status code."""
        error = APIError(message="Test error")
        
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.error_code == "INTERNAL_ERROR"

    def test_api_error_default_details(self):
        """Test APIError default details."""
        error = APIError(message="Test error")
        
        assert error.details == {}

    def test_api_error_str_representation(self):
        """Test APIError string representation."""
        error = APIError(message="Test error message")
        
        assert str(error) == "Test error message"

    def test_api_error_inherits_exception(self):
        """Test APIError inherits from Exception."""
        error = APIError(message="Test")
        
        assert isinstance(error, Exception)


class TestBadRequestError:
    """Test suite for BadRequestError class."""

    def test_bad_request_error_default_message(self):
        """Test BadRequestError with default message."""
        error = BadRequestError()
        
        assert error.message == "Bad request"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_code == "BAD_REQUEST"

    def test_bad_request_error_custom_message(self):
        """Test BadRequestError with custom message."""
        error = BadRequestError(message="Invalid input")
        
        assert error.message == "Invalid input"
        assert error.status_code == status.HTTP_400_BAD_REQUEST

    def test_bad_request_error_with_details(self):
        """Test BadRequestError with details."""
        details = {"field": "email", "reason": "Invalid format"}
        error = BadRequestError(message="Validation failed", details=details)
        
        assert error.details == details


class TestUnauthorizedError:
    """Test suite for UnauthorizedError class."""

    def test_unauthorized_error_default(self):
        """Test UnauthorizedError with defaults."""
        error = UnauthorizedError()
        
        assert error.message == "Unauthorized"
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.error_code == "UNAUTHORIZED"

    def test_unauthorized_error_custom_message(self):
        """Test UnauthorizedError with custom message."""
        error = UnauthorizedError(message="Invalid token")
        
        assert error.message == "Invalid token"

    def test_unauthorized_error_with_details(self):
        """Test UnauthorizedError with details."""
        error = UnauthorizedError(
            message="Token expired", details={"expired_at": "2024-01-01"}
        )
        
        assert error.details["expired_at"] == "2024-01-01"


class TestForbiddenError:
    """Test suite for ForbiddenError class."""

    def test_forbidden_error_default(self):
        """Test ForbiddenError with defaults."""
        error = ForbiddenError()
        
        assert error.message == "Forbidden"
        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.error_code == "FORBIDDEN"

    def test_forbidden_error_custom_message(self):
        """Test ForbiddenError with custom message."""
        error = ForbiddenError(message="Insufficient permissions")
        
        assert error.message == "Insufficient permissions"

    def test_forbidden_error_with_details(self):
        """Test ForbiddenError with details."""
        error = ForbiddenError(
            message="Access denied", details={"required_role": "admin"}
        )
        
        assert error.details["required_role"] == "admin"


class TestNotFoundError:
    """Test suite for NotFoundError class."""

    def test_not_found_error_default(self):
        """Test NotFoundError with defaults."""
        error = NotFoundError()
        
        assert error.message == "Resource not found"
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.error_code == "NOT_FOUND"

    def test_not_found_error_custom_message(self):
        """Test NotFoundError with custom message."""
        error = NotFoundError(message="User not found")
        
        assert error.message == "User not found"

    def test_not_found_error_with_details(self):
        """Test NotFoundError with details."""
        error = NotFoundError(
            message="Project not found", details={"project_id": "123"}
        )
        
        assert error.details["project_id"] == "123"


class TestConflictError:
    """Test suite for ConflictError class."""

    def test_conflict_error_default(self):
        """Test ConflictError with defaults."""
        error = ConflictError()
        
        assert error.message == "Resource conflict"
        assert error.status_code == status.HTTP_409_CONFLICT
        assert error.error_code == "CONFLICT"

    def test_conflict_error_custom_message(self):
        """Test ConflictError with custom message."""
        error = ConflictError(message="Email already exists")
        
        assert error.message == "Email already exists"

    def test_conflict_error_with_details(self):
        """Test ConflictError with details."""
        error = ConflictError(
            message="Duplicate entry", details={"field": "username", "value": "john"}
        )
        
        assert error.details["field"] == "username"


class TestValidationErrorException:
    """Test suite for ValidationErrorException class."""

    def test_validation_error_default(self):
        """Test ValidationErrorException with defaults."""
        error = ValidationErrorException()
        
        assert error.message == "Validation error"
        assert error.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert error.error_code == "VALIDATION_ERROR"

    def test_validation_error_custom_message(self):
        """Test ValidationErrorException with custom message."""
        error = ValidationErrorException(message="Invalid email format")
        
        assert error.message == "Invalid email format"

    def test_validation_error_with_details(self):
        """Test ValidationErrorException with details."""
        details = {"errors": [{"field": "email", "message": "Invalid format"}]}
        error = ValidationErrorException(message="Validation failed", details=details)
        
        assert "errors" in error.details


class TestRateLimitError:
    """Test suite for RateLimitError class."""

    def test_rate_limit_error_default(self):
        """Test RateLimitError with defaults."""
        error = RateLimitError()
        
        assert error.message == "Rate limit exceeded"
        assert error.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert error.error_code == "RATE_LIMIT_EXCEEDED"
        assert error.details["retry_after"] == 60

    def test_rate_limit_error_custom_message(self):
        """Test RateLimitError with custom message."""
        error = RateLimitError(message="Too many requests")
        
        assert error.message == "Too many requests"

    def test_rate_limit_error_custom_retry_after(self):
        """Test RateLimitError with custom retry_after."""
        error = RateLimitError(retry_after=120)
        
        assert error.details["retry_after"] == 120

    def test_rate_limit_error_both_parameters(self):
        """Test RateLimitError with both message and retry_after."""
        error = RateLimitError(message="API limit reached", retry_after=300)
        
        assert error.message == "API limit reached"
        assert error.details["retry_after"] == 300


class TestServiceUnavailableError:
    """Test suite for ServiceUnavailableError class."""

    def test_service_unavailable_error_default(self):
        """Test ServiceUnavailableError with defaults."""
        error = ServiceUnavailableError()
        
        assert error.message == "Service unavailable"
        assert error.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert error.error_code == "SERVICE_UNAVAILABLE"

    def test_service_unavailable_error_custom_message(self):
        """Test ServiceUnavailableError with custom message."""
        error = ServiceUnavailableError(message="Database is down")
        
        assert error.message == "Database is down"

    def test_service_unavailable_error_with_details(self):
        """Test ServiceUnavailableError with details."""
        error = ServiceUnavailableError(
            message="Maintenance mode", details={"scheduled_until": "2024-01-01"}
        )
        
        assert error.details["scheduled_until"] == "2024-01-01"


class TestCreateErrorResponse:
    """Test suite for create_error_response function."""

    def test_create_error_response_basic(self):
        """Test creating basic error response."""
        response = create_error_response(
            status_code=400, message="Bad request", error_code="BAD_REQUEST"
        )
        
        assert response.status_code == 400
        content = response.body.decode()
        assert "Bad request" in content
        assert "BAD_REQUEST" in content

    def test_create_error_response_with_details(self):
        """Test creating error response with details."""
        details = {"field": "email", "reason": "Invalid format"}
        response = create_error_response(
            status_code=400,
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details=details,
        )
        
        content = response.body.decode()
        assert "email" in content
        assert "Invalid format" in content

    def test_create_error_response_with_path(self):
        """Test creating error response with path."""
        response = create_error_response(
            status_code=404,
            message="Not found",
            error_code="NOT_FOUND",
            path="/api/v1/users/123",
        )
        
        content = response.body.decode()
        assert "/api/v1/users/123" in content

    def test_create_error_response_without_error_code(self):
        """Test creating error response without specific error code."""
        response = create_error_response(status_code=500, message="Internal error")
        
        content = response.body.decode()
        assert "ERROR" in content  # Default error code

    def test_create_error_response_structure(self):
        """Test error response has correct structure."""
        import json
        
        response = create_error_response(
            status_code=400,
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            path="/api/test",
        )
        
        content = json.loads(response.body.decode())
        
        assert "error" in content
        assert "code" in content["error"]
        assert "message" in content["error"]
        assert "status" in content["error"]
        assert "details" in content["error"]
        assert "path" in content["error"]
        assert content["error"]["code"] == "TEST_ERROR"
        assert content["error"]["message"] == "Test error"
        assert content["error"]["status"] == 400

    def test_create_error_response_without_details(self):
        """Test error response without details."""
        import json
        
        response = create_error_response(status_code=404, message="Not found")
        
        content = json.loads(response.body.decode())
        
        assert "details" not in content["error"]

    def test_create_error_response_without_path(self):
        """Test error response without path."""
        import json
        
        response = create_error_response(status_code=500, message="Server error")
        
        content = json.loads(response.body.decode())
        
        assert "path" not in content["error"]

    def test_create_error_response_various_status_codes(self):
        """Test error responses with various status codes."""
        status_codes = [400, 401, 403, 404, 409, 422, 429, 500, 503]
        
        for code in status_codes:
            response = create_error_response(
                status_code=code, message=f"Error {code}"
            )
            assert response.status_code == code
