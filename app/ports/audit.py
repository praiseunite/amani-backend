"""Audit port interface."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime


class AuditPort(ABC):
    """Port interface for audit logging operations."""

    @abstractmethod
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
        pass
