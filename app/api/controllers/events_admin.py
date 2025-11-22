"""Events admin controller for testing."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.ports.event_publisher import EventPublisherPort


class TestEventRequest(BaseModel):
    """Request model for publishing a test event."""

    topic: str
    event_type: str
    payload: Dict[str, Any]


class TestEventResponse(BaseModel):
    """Response model for test event publishing."""

    success: bool
    message: str


def create_events_admin_router(event_publisher: EventPublisherPort):
    """Create events admin router.

    Args:
        event_publisher: Port for publishing events

    Returns:
        FastAPI router
    """
    router = APIRouter(prefix="/events", tags=["events"])

    @router.post("/test", response_model=TestEventResponse)
    async def publish_test_event(request: TestEventRequest):
        """Publish a test event.

        Args:
            request: Test event request

        Returns:
            Test event response
        """
        await event_publisher.publish(
            topic=request.topic,
            event_type=request.event_type,
            payload=request.payload,
        )

        return TestEventResponse(
            success=True,
            message="Event published successfully",
        )

    return router
