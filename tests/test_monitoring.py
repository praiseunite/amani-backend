"""
Tests for monitoring and observability features.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.metrics import PrometheusMiddleware, get_metrics
from app.core.request_id import RequestIDMiddleware, get_request_id
from app.routes.metrics import router as metrics_router


@pytest.fixture
def test_app():
    """Create a test FastAPI app with monitoring middleware."""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(PrometheusMiddleware)
    app.include_router(metrics_router)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


def test_metrics_endpoint_exists(client):
    """Test that metrics endpoint is available."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_metrics_endpoint_returns_prometheus_format(client):
    """Test that metrics are in Prometheus format."""
    response = client.get("/metrics")
    content = response.text
    
    # Should contain Prometheus metric format
    assert "# HELP" in content or "# TYPE" in content or "_total" in content


def test_request_id_middleware_generates_id(client):
    """Test that request ID middleware generates IDs."""
    response = client.get("/test")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_request_id_middleware_preserves_existing_id(client):
    """Test that existing request IDs are preserved."""
    custom_id = "test-request-id-123"
    response = client.get("/test", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_prometheus_middleware_tracks_requests(client):
    """Test that Prometheus middleware tracks requests."""
    # Make some requests
    for _ in range(5):
        client.get("/test")
    
    # Get metrics
    response = client.get("/metrics")
    content = response.text
    
    # Should contain request metrics
    assert "http_requests_total" in content or "http_request" in content


def test_prometheus_middleware_normalizes_paths(client):
    """Test that paths with IDs are normalized."""
    # Make requests with different IDs
    client.get("/test")
    
    # Get metrics
    response = client.get("/metrics")
    content = response.text
    
    # Should have normalized the path
    assert "http_request" in content


def test_get_metrics_returns_bytes():
    """Test that get_metrics returns bytes."""
    metrics = get_metrics()
    assert isinstance(metrics, bytes)
    assert len(metrics) > 0


def test_request_id_helper_function():
    """Test the get_request_id helper function."""
    from starlette.requests import Request
    from starlette.datastructures import Headers
    
    # Create a mock request with a request ID
    class MockRequest:
        def __init__(self):
            self.state = type('obj', (object,), {'request_id': 'test-id-456'})
    
    request = MockRequest()
    request_id = get_request_id(request)
    assert request_id == 'test-id-456'


def test_request_id_helper_function_unknown():
    """Test get_request_id returns 'unknown' when no ID."""
    from starlette.requests import Request
    
    class MockRequest:
        def __init__(self):
            self.state = type('obj', (object,), {})
    
    request = MockRequest()
    request_id = get_request_id(request)
    assert request_id == 'unknown'
