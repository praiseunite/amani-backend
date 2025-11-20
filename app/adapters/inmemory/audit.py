"""In-memory audit implementation for testing."""

from typing import Any, Dict, List
from uuid import UUID
from datetime import datetime

from app.ports.audit import AuditPort


class InMemoryAudit(AuditPort):
    """In-memory implementation of audit logging."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._events: List[Dict[str, Any]] = []

    async def record(
        self,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any],
    ) -> None:
        """Record an audit event.

        Args:
            user_id: The user performing the action
            action: The action being performed
            resource_type: The type of resource affected
            resource_id: The ID of the resource affected
            details: Additional details about the action
        """
        event = {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._events.append(event)

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all recorded events (for testing).

        Returns:
            List of recorded events
        """
        return self._events
