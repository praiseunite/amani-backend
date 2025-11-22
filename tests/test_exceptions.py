"""
Tests for custom exception handlers.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
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
    register_exception_handlers,
)


@pytest.fixture
def test_app():
    """Create test FastAPI application."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test/bad-request")
    async def bad_request_endpoint():
        raise BadRequestError("Invalid request")

    @app.get("/test/unauthorized")
    async def unauthorized_endpoint():
        raise UnauthorizedError("Not authenticated")

    @app.get("/test/forbidden")
    async def forbidden_endpoint():
        raise ForbiddenError("Access denied")

    @app.get("/test/not-found")
    async def not_found_endpoint():
        raise NotFoundError("Resource not found")

    @app.get("/test/conflict")
    async def conflict_endpoint():
        raise ConflictError("Resource conflict")

    @app.get("/test/validation-error")
    async def validation_error_endpoint():
        raise ValidationErrorException("Validation failed")

    @app.get("/test/rate-limit")
    async def rate_limit_endpoint():
        raise RateLimitError("Too many requests", retry_after=120)

    @app.get("/test/service-unavailable")
    async def service_unavailable_endpoint():
        raise ServiceUnavailableError("Service down")

    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestExceptionHandlers:
    """Test exception handlers."""

    def test_bad_request_error(self, client):
        """Test bad request error handler."""
        response = client.get("/test/bad-request")
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "BAD_REQUEST"
        assert "Invalid request" in data["error"]["message"]

    def test_unauthorized_error(self, client):
        """Test unauthorized error handler."""
        response = client.get("/test/unauthorized")
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_forbidden_error(self, client):
        """Test forbidden error handler."""
        response = client.get("/test/forbidden")
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "FORBIDDEN"

    def test_not_found_error(self, client):
        """Test not found error handler."""
        response = client.get("/test/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"

    def test_conflict_error(self, client):
        """Test conflict error handler."""
        response = client.get("/test/conflict")
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "CONFLICT"

    def test_validation_error(self, client):
        """Test validation error handler."""
        response = client.get("/test/validation-error")
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_rate_limit_error(self, client):
        """Test rate limit error handler."""
        response = client.get("/test/rate-limit")
        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert data["error"]["details"]["retry_after"] == 120

    def test_service_unavailable_error(self, client):
        """Test service unavailable error handler."""
        response = client.get("/test/service-unavailable")
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"


class TestAPIErrorClass:
    """Test APIError base class."""

    def test_api_error_initialization(self):
        """Test APIError initialization."""
        error = APIError(
            message="Test error", status_code=400, error_code="TEST_ERROR", details={"key": "value"}
        )

        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}

    def test_api_error_default_values(self):
        """Test APIError default values."""
        error = APIError(message="Test error")

        assert error.status_code == 500
        assert error.error_code == "INTERNAL_ERROR"
        assert error.details == {}
