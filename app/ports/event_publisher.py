"""Event publisher port interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class EventPublisherPort(ABC):
    """Port for publishing domain events."""

    @abstractmethod
    async def publish(self, topic: str, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event.

        Args:
            topic: The topic to publish to
            event_type: The type of event
            payload: The event data
        """
        pass
