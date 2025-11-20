"""In-memory implementation of AuditPort for testing."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field

from app.ports.audit import AuditPort


@dataclass
class AuditEvent:
    """Represents an audit event."""

    event_type: str
    user_id: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class InMemoryAuditLog(AuditPort):
    """In-memory implementation of the audit log."""

    def __init__(self):
        """Initialize the in-memory audit log."""
        self._events: List[AuditEvent] = []

    async def record(
        self,
        event_type: str,
        user_id: Optional[str],
        details: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record an audit event.

        Args:
            event_type: The type of event being audited.
            user_id: The user ID associated with the event (if applicable).
            details: Additional details about the event.
            timestamp: The timestamp of the event (defaults to current time).
        """
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            details=details,
            timestamp=timestamp or datetime.utcnow(),
        )
        self._events.append(event)

    def get_events(self) -> List[AuditEvent]:
        """Get all recorded audit events.

        Returns:
            A list of all audit events.
        """
        return self._events.copy()

    def clear(self) -> None:
        """Clear all audit events."""
        self._events.clear()
