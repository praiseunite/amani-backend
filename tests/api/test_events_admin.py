"""Tests for events admin endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.composition import build_app_components


@pytest.fixture
def components():
    """Build application components."""
    return build_app_components()


@pytest.fixture
def client(components):
    """Create test client."""
    app = create_app(components)
    return TestClient(app)


@pytest.fixture
def event_publisher(components):
    """Get event publisher."""
    return components["event_publisher_port"]


class TestEventsAdmin:
    """Test suite for events admin endpoint."""

    @pytest.mark.asyncio
    async def test_publish_test_event(self, client, event_publisher):
        """Test publishing a test event."""
        # Make request
        response = client.post(
            "/api/v1/events/test",
            json={
                "topic": "user.events",
                "event_type": "user.created",
                "payload": {"user_id": "123", "email": "test@example.com"},
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Event published successfully"

        # Verify event was published
        events = event_publisher.get_events()
        assert len(events) == 1
        assert events[0]["topic"] == "user.events"
        assert events[0]["event_type"] == "user.created"
        assert events[0]["payload"]["user_id"] == "123"
