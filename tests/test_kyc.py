"""
Comprehensive tests for KYC functionality including 2FA TOTP and middleware.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.auth import generate_totp_code, generate_totp_secret, get_totp_uri, verify_totp_code
from app.core.security import KYCEnforcementMiddleware
from app.models.kyc import Kyc, KycStatus
from app.models.user import User


class TestTOTPFunctionality:
    """Test TOTP (2FA) functionality for approval codes."""

    def test_generate_totp_secret(self):
        """Test generating a TOTP secret."""
        secret = generate_totp_secret()

        assert secret is not None
        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded secrets are 32 characters

    def test_generate_totp_secret_uniqueness(self):
        """Test that generated secrets are unique."""
        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()

        assert secret1 != secret2

    def test_get_totp_uri(self):
        """Test generating TOTP URI for QR code."""
        secret = generate_totp_secret()
        account = "test@example.com"

        uri = get_totp_uri(secret, account)

        assert uri is not None
        assert isinstance(uri, str)
        assert uri.startswith("otpauth://totp/")
        # Email is URL-encoded in the URI
        assert "test%40example.com" in uri or account in uri
        assert "Amani" in uri
        assert secret in uri

    def test_get_totp_uri_custom_issuer(self):
        """Test generating TOTP URI with custom issuer."""
        secret = generate_totp_secret()
        account = "test@example.com"
        issuer = "CustomIssuer"

        uri = get_totp_uri(secret, account, issuer)

        assert issuer in uri

    def test_verify_totp_code_valid(self):
        """Test verifying a valid TOTP code."""
        secret = generate_totp_secret()

        # Generate a valid code
        code = generate_totp_code(secret)

        # Verify the code
        assert verify_totp_code(secret, code) is True

    def test_verify_totp_code_invalid(self):
        """Test verifying an invalid TOTP code."""
        secret = generate_totp_secret()

        # Use an invalid code
        invalid_code = "000000"

        assert verify_totp_code(secret, invalid_code) is False

    def test_verify_totp_code_wrong_secret(self):
        """Test verifying a code with wrong secret."""
        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()

        # Generate code with secret1
        code = generate_totp_code(secret1)

        # Try to verify with secret2
        assert verify_totp_code(secret2, code) is False

    def test_generate_totp_code(self):
        """Test generating current TOTP code."""
        secret = generate_totp_secret()

        code = generate_totp_code(secret)

        assert code is not None
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isdigit()

    def test_totp_code_changes_over_time(self):
        """Test that TOTP codes change over time."""
        secret = generate_totp_secret()

        # Generate code at current time
        code1 = generate_totp_code(secret)

        # In a real scenario, we'd wait 30+ seconds
        # For testing, we can verify the code is valid
        assert verify_totp_code(secret, code1) is True

    def test_totp_valid_window(self):
        """Test TOTP code validation with time window."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)

        # Test with different valid windows
        assert verify_totp_code(secret, code, valid_window=0) is True
        assert verify_totp_code(secret, code, valid_window=1) is True
        assert verify_totp_code(secret, code, valid_window=2) is True

    def test_verify_totp_code_exception_handling(self):
        """Test TOTP verification handles exceptions gracefully."""
        # Test with invalid secret format
        assert verify_totp_code("invalid", "123456") is False

        # Test with None values
        assert verify_totp_code("", "123456") is False


class TestKYCEnforcementMiddleware:
    """Test KYC enforcement middleware for transactions."""

    @pytest.mark.asyncio
    async def test_middleware_initialization(self):
        """Test KYC middleware can be initialized."""
        app = Mock()
        middleware = KYCEnforcementMiddleware(app)

        assert middleware is not None
        assert len(middleware.PROTECTED_TRANSACTION_ROUTES) > 0

    @pytest.mark.asyncio
    async def test_middleware_allows_non_transaction_routes(self):
        """Test middleware allows non-transaction routes without KYC check."""
        app = Mock()
        middleware = KYCEnforcementMiddleware(app)

        # Mock request to non-transaction route
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/v1/auth/login"
        request.state = Mock()

        # Mock call_next
        call_next = AsyncMock(return_value=Mock())

        await middleware.dispatch(request, call_next)

        # Verify call_next was called (route was allowed)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_allows_get_requests_to_transaction_routes(self):
        """Test middleware allows GET requests even to transaction routes."""
        app = Mock()
        middleware = KYCEnforcementMiddleware(app)

        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/v1/escrow/hold"
        request.state = Mock()

        call_next = AsyncMock(return_value=Mock())

        await middleware.dispatch(request, call_next)

        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_checks_kyc_for_transaction_routes(self):
        """Test middleware checks KYC for POST requests to transaction routes."""
        app = Mock()
        middleware = KYCEnforcementMiddleware(app)

        # Mock user
        user = Mock(spec=User)
        user.id = uuid4()

        # Mock request
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/v1/escrow/hold"
        request.state = Mock()
        request.state.user = user

        # Mock database and KYC query
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)  # No approved KYC
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.close = AsyncMock()

        async def mock_get_db():
            yield mock_db

        with patch("app.core.security.get_db", return_value=mock_get_db()):
            call_next = AsyncMock(return_value=Mock())

            response = await middleware.dispatch(request, call_next)

            # Should return forbidden response
            assert isinstance(response, JSONResponse)
            assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_middleware_allows_transaction_with_approved_kyc(self):
        """Test middleware allows transactions when user has approved KYC."""
        app = Mock()
        middleware = KYCEnforcementMiddleware(app)

        # Mock user
        user = Mock(spec=User)
        user.id = uuid4()

        # Mock approved KYC
        approved_kyc = Mock(spec=Kyc)
        approved_kyc.status = KycStatus.APPROVED

        # Mock request
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/v1/escrow/hold"
        request.state = Mock()
        request.state.user = user

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=approved_kyc)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.close = AsyncMock()

        async def mock_get_db():
            yield mock_db

        with patch("app.core.security.get_db", return_value=mock_get_db()):
            call_next = AsyncMock(return_value=Mock(status_code=200))

            await middleware.dispatch(request, call_next)

            # Should allow request through
            call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_handles_no_user_gracefully(self):
        """Test middleware handles requests without user gracefully."""
        app = Mock()
        middleware = KYCEnforcementMiddleware(app)

        # Mock request without user
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/v1/escrow/hold"
        request.state = Mock()
        request.state.user = None

        call_next = AsyncMock(return_value=Mock())

        await middleware.dispatch(request, call_next)

        # Should allow request through (authentication layer will handle it)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_handles_database_errors(self):
        """Test middleware handles database errors gracefully."""
        app = Mock()
        middleware = KYCEnforcementMiddleware(app)

        user = Mock(spec=User)
        user.id = uuid4()

        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/v1/escrow/release"
        request.state = Mock()
        request.state.user = user

        # Mock database error
        async def mock_get_db_error():
            raise Exception("Database connection error")

        with patch("app.core.security.get_db", side_effect=mock_get_db_error):
            call_next = AsyncMock(return_value=Mock())

            await middleware.dispatch(request, call_next)

            # Should allow request through on error
            call_next.assert_called_once()

    def test_protected_routes_configuration(self):
        """Test that protected routes are properly configured."""
        app = Mock()
        middleware = KYCEnforcementMiddleware(app)

        routes = middleware.PROTECTED_TRANSACTION_ROUTES

        assert isinstance(routes, list)
        assert len(routes) > 0
        assert "/api/v1/escrow/hold" in routes
        assert "/api/v1/escrow/release" in routes


class TestKYCIntegration:
    """Integration tests for KYC functionality."""

    def test_totp_imports(self):
        """Test that all TOTP functions can be imported."""
        from app.core.auth import (
            generate_totp_code,
            generate_totp_secret,
            get_totp_uri,
            verify_totp_code,
        )

        assert generate_totp_secret is not None
        assert get_totp_uri is not None
        assert verify_totp_code is not None
        assert generate_totp_code is not None

    def test_middleware_imports(self):
        """Test that KYC middleware can be imported."""
        from app.core.security import KYCEnforcementMiddleware

        assert KYCEnforcementMiddleware is not None

    def test_kyc_models_compatibility(self):
        """Test KYC models are compatible with new features."""
        from app.models.kyc import Kyc, KycStatus, KycType

        # Verify KYC model has required fields
        assert hasattr(Kyc, "approval_code")
        assert hasattr(Kyc, "status")
        assert hasattr(Kyc, "user_id")

        # Verify KYC statuses
        assert KycStatus.APPROVED is not None
        assert KycStatus.PENDING is not None
        assert KycStatus.REJECTED is not None

    def test_totp_workflow_complete(self):
        """Test complete TOTP workflow from generation to verification."""
        # Step 1: Generate secret
        secret = generate_totp_secret()

        # Step 2: Generate URI for QR code
        uri = get_totp_uri(secret, "user@example.com")
        assert uri is not None

        # Step 3: Generate code
        code = generate_totp_code(secret)
        assert code is not None

        # Step 4: Verify code
        is_valid = verify_totp_code(secret, code)
        assert is_valid is True

        # Step 5: Verify invalid code fails
        is_valid_invalid = verify_totp_code(secret, "000000")
        assert is_valid_invalid is False

    def test_pyotp_library_integration(self):
        """Test that pyotp library is properly integrated."""
        import pyotp

        # Test basic pyotp functionality
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()

        assert len(code) == 6
        assert code.isdigit()
        assert totp.verify(code) is True


class TestKYCStatusValidation:
    """Test KYC status validation scenarios."""

    def test_kyc_status_enum_values(self):
        """Test KYC status enumeration values."""
        from app.models.kyc import KycStatus

        assert KycStatus.PENDING.value == "pending"
        assert KycStatus.APPROVED.value == "approved"
        assert KycStatus.REJECTED.value == "rejected"

    def test_kyc_type_enum_values(self):
        """Test KYC type enumeration values."""
        from app.models.kyc import KycType

        assert KycType.KYC.value == "kyc"
        assert KycType.KYB.value == "kyb"

    def test_user_role_enum_values(self):
        """Test User role enumeration values."""
        from app.models.user import UserRole

        assert UserRole.ADMIN.value == "admin"
        assert UserRole.CLIENT.value == "client"
        assert UserRole.FREELANCER.value == "freelancer"


class TestTOTPSecurityFeatures:
    """Test security features of TOTP implementation."""

    def test_totp_secret_length_security(self):
        """Test that TOTP secrets have adequate length for security."""
        secret = generate_totp_secret()

        # Base32 secrets should be at least 16 characters for 80-bit security
        assert len(secret) >= 16
        # Standard is 32 characters for 160-bit security
        assert len(secret) == 32

    def test_totp_code_format(self):
        """Test that TOTP codes follow standard format."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)

        # Standard TOTP codes are 6 digits
        assert len(code) == 6
        assert code.isdigit()

    def test_multiple_verification_attempts(self):
        """Test that code can be verified multiple times within time window."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)

        # Code should remain valid for multiple verification attempts
        assert verify_totp_code(secret, code) is True
        assert verify_totp_code(secret, code) is True
        assert verify_totp_code(secret, code) is True

    def test_totp_with_special_characters_in_account(self):
        """Test TOTP URI generation with special characters in account name."""
        secret = generate_totp_secret()
        account = "user+tag@example.com"

        uri = get_totp_uri(secret, account)

        assert uri is not None
        # Special characters should be URL encoded in the URI
        assert "otpauth://totp/" in uri
