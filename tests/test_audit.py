"""
Tests for audit logging functionality.
"""
import pytest
from uuid import uuid4
from app.core.audit import (
    AuditLogger,
    AuditAction,
    AuditLevel,
    audit_log
)


class TestAuditLogger:
    """Test audit logging functionality."""
    
    def test_log_authentication_success(self):
        """Test logging successful authentication."""
        user_id = uuid4()
        user_email = "test@example.com"
        
        # Should not raise exception
        AuditLogger.log_authentication(
            action=AuditAction.USER_LOGIN,
            user_id=user_id,
            user_email=user_email,
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            success=True
        )
    
    def test_log_authentication_failure(self):
        """Test logging failed authentication."""
        # Should not raise exception
        AuditLogger.log_authentication(
            action=AuditAction.USER_LOGIN,
            user_email="test@example.com",
            ip_address="127.0.0.1",
            success=False,
            error_message="Invalid credentials"
        )
    
    def test_log_payment_event(self):
        """Test logging payment event."""
        user_id = uuid4()
        
        # Should not raise exception
        AuditLogger.log_payment(
            action=AuditAction.PAYMENT_INITIATED,
            user_id=user_id,
            user_email="test@example.com",
            amount=100.50,
            currency="USD",
            transaction_id="txn_123",
            project_id="proj_456",
            ip_address="127.0.0.1",
            success=True
        )
    
    def test_log_security_event(self):
        """Test logging security event."""
        # Should not raise exception
        AuditLogger.log_security_event(
            action=AuditAction.RATE_LIMIT_EXCEEDED,
            ip_address="192.168.1.1",
            details={"requests": 150, "limit": 100},
            level=AuditLevel.WARNING
        )
    
    def test_log_data_access(self):
        """Test logging data access."""
        user_id = uuid4()
        
        # Should not raise exception
        AuditLogger.log_data_access(
            action=AuditAction.DATA_EXPORTED,
            user_id=user_id,
            user_email="test@example.com",
            resource_type="project",
            resource_id="proj_789",
            ip_address="127.0.0.1",
            details={"format": "csv", "records": 100}
        )
    
    def test_audit_log_convenience_function(self):
        """Test convenience function for audit logging."""
        user_id = uuid4()
        
        # Should not raise exception
        audit_log(
            action=AuditAction.PROJECT_CREATED,
            user_id=user_id,
            user_email="test@example.com",
            resource_type="project",
            resource_id="proj_999",
            ip_address="127.0.0.1"
        )
    
    def test_log_event_with_all_parameters(self):
        """Test logging event with all parameters."""
        user_id = uuid4()
        
        # Should not raise exception
        AuditLogger.log_event(
            action=AuditAction.PROJECT_UPDATED,
            user_id=user_id,
            user_email="test@example.com",
            resource_type="project",
            resource_id="proj_111",
            details={"field": "status", "old_value": "active", "new_value": "completed"},
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            level=AuditLevel.INFO,
            success=True
        )
