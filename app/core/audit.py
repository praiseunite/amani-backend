"""
Audit trail system for tracking sensitive operations and user actions.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Enumeration of auditable actions."""

    # Authentication actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"

    # Authorization actions
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGED = "role_changed"

    # Project actions
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    PROJECT_STATUS_CHANGED = "project_status_changed"

    # Milestone actions
    MILESTONE_CREATED = "milestone_created"
    MILESTONE_UPDATED = "milestone_updated"
    MILESTONE_DELETED = "milestone_deleted"
    MILESTONE_COMPLETED = "milestone_completed"

    # Payment/Escrow actions
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    FUNDS_DEPOSITED = "funds_deposited"
    FUNDS_RELEASED = "funds_released"
    FUNDS_REFUNDED = "funds_refunded"

    # Security actions
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Data actions
    DATA_EXPORTED = "data_exported"
    DATA_DELETED = "data_deleted"


class AuditLevel(str, Enum):
    """Audit log severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """
    Centralized audit logging system.
    Logs sensitive operations with structured data for compliance and security.
    """

    @staticmethod
    def log_event(
        action: AuditAction,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        level: AuditLevel = AuditLevel.INFO,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """
        Log an audit event.

        Args:
            action: The action being audited
            user_id: ID of the user performing the action
            user_email: Email of the user performing the action
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource being acted upon
            details: Additional details about the event
            ip_address: IP address of the client
            user_agent: User agent string
            level: Severity level of the audit event
            success: Whether the action was successful
            error_message: Error message if action failed
        """
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action.value,
            "level": level.value,
            "success": success,
            "user_id": str(user_id) if user_id else None,
            "user_email": user_email,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {},
            "error_message": error_message,
        }

        # Log based on level
        if level == AuditLevel.CRITICAL:
            logger.critical("AUDIT", extra=audit_data)
        elif level == AuditLevel.ERROR:
            logger.error("AUDIT", extra=audit_data)
        elif level == AuditLevel.WARNING:
            logger.warning("AUDIT", extra=audit_data)
        else:
            logger.info("AUDIT", extra=audit_data)

    @staticmethod
    def log_authentication(
        action: AuditAction,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """
        Log authentication-related events.

        Args:
            action: Authentication action
            user_id: User ID
            user_email: User email
            ip_address: Client IP address
            user_agent: User agent string
            success: Whether authentication was successful
            error_message: Error message if failed
        """
        AuditLogger.log_event(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type="authentication",
            ip_address=ip_address,
            user_agent=user_agent,
            level=AuditLevel.WARNING if not success else AuditLevel.INFO,
            success=success,
            error_message=error_message,
        )

    @staticmethod
    def log_payment(
        action: AuditAction,
        user_id: UUID,
        user_email: str,
        amount: float,
        currency: str,
        transaction_id: Optional[str] = None,
        project_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """
        Log payment-related events.

        Args:
            action: Payment action
            user_id: User ID
            user_email: User email
            amount: Payment amount
            currency: Currency code
            transaction_id: Transaction ID
            project_id: Related project ID
            ip_address: Client IP address
            success: Whether payment was successful
            error_message: Error message if failed
        """
        AuditLogger.log_event(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type="payment",
            resource_id=transaction_id,
            details={"amount": amount, "currency": currency, "project_id": project_id},
            ip_address=ip_address,
            level=AuditLevel.ERROR if not success else AuditLevel.INFO,
            success=success,
            error_message=error_message,
        )

    @staticmethod
    def log_security_event(
        action: AuditAction,
        ip_address: Optional[str] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.WARNING,
    ):
        """
        Log security-related events.

        Args:
            action: Security action
            ip_address: Client IP address
            user_id: User ID if applicable
            user_email: User email if applicable
            details: Additional details
            level: Severity level
        """
        AuditLogger.log_event(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type="security",
            details=details,
            ip_address=ip_address,
            level=level,
            success=False,  # Security events are typically failures
        )

    @staticmethod
    def log_data_access(
        action: AuditAction,
        user_id: UUID,
        user_email: str,
        resource_type: str,
        resource_id: str,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log data access events.

        Args:
            action: Data action
            user_id: User ID
            user_email: User email
            resource_type: Type of resource accessed
            resource_id: Resource ID
            ip_address: Client IP address
            details: Additional details
        """
        AuditLogger.log_event(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            level=AuditLevel.INFO,
        )


# Convenience function for quick audit logging
def audit_log(
    action: AuditAction, user_id: Optional[UUID] = None, user_email: Optional[str] = None, **kwargs
):
    """
    Convenience function for audit logging.

    Args:
        action: Action to audit
        user_id: User ID
        user_email: User email
        **kwargs: Additional arguments passed to AuditLogger.log_event
    """
    AuditLogger.log_event(action=action, user_id=user_id, user_email=user_email, **kwargs)
