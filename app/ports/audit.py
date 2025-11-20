"""Audit port - interface for audit logging."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID


class AuditPort(ABC):
    """Port for audit operations."""

    @abstractmethod
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
        pass
