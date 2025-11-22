"""In-memory event publisher adapter."""

from typing import Any, Dict, List

from app.ports.event_publisher import EventPublisherPort


class InMemoryEventPublisher(EventPublisherPort):
    """In-memory implementation of event publisher for testing."""

    def __init__(self):
        """Initialize in-memory event publisher."""
        self.events: List[Dict[str, Any]] = []

    async def publish(self, topic: str, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event.

        Args:
            topic: The topic to publish to
            event_type: The type of event
            payload: The event data
        """
        self.events.append({"topic": topic, "event_type": event_type, "payload": payload})

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all published events.

        Returns:
            List of published events
        """
        return self.events

    def clear(self) -> None:
        """Clear all events."""
        self.events = []
