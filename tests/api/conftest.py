"""Shared fixtures for API tests."""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.api.app import build_fastapi_app
from app.composition import build_app_components
from app.domain.entities import User


@pytest.fixture
def components():
    """Build application components for testing."""
    return build_app_components()


@pytest.fixture
def client(components):
    """Create test client with in-memory dependencies."""
    app = build_fastapi_app(components)
    return TestClient(app)


@pytest.fixture
def test_user(components):
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        role="client",
        is_active=True,
        is_verified=True,
    )
    # Save user to repository
    import asyncio

    asyncio.run(components["user_repository_port"].save(user))
    return user


@pytest.fixture
def api_key(components):
    """Add test API key."""
    key_id = "test-key-id"
    secret = "test-secret"
    components["api_key_port"].add_key(key_id, secret)
    return {"key_id": key_id, "secret": secret}
