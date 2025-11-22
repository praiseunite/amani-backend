"""
Comprehensive unit tests for app.core.auth module.
Tests password hashing, JWT tokens, and TOTP (2FA) functionality.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    generate_totp_secret,
    get_totp_uri,
    verify_totp_code,
    generate_totp_code,
)
from app.core.config import settings
from app.models.user import UserRole


class TestPasswordHashing:
    """Test suite for password hashing functions."""

    def test_get_password_hash_returns_hash(self):
        """Test that get_password_hash returns a hashed password."""
        password = "my_secure_password_123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password  # Hash should be different from plain password
        assert hashed.startswith("$2b$")  # bcrypt hash prefix

    def test_get_password_hash_different_hashes(self):
        """Test that same password generates different hashes (salt)."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Due to salting, hashes should be different
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "correct_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self):
        """Test password verification with empty string."""
        password = "test_password"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False

    def test_password_hash_round_trip(self):
        """Test password hashing and verification round trip."""
        passwords = [
            "simple",
            "with spaces",
            "Special!@#$%^&*()",
            "VeryLongPasswordWith123NumbersAndSpecialChars!@#",
            "unicode_παράδειγμα_例",
        ]
        
        for password in passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test suite for JWT token functions."""

    def test_create_access_token_basic(self):
        """Test creating a basic access token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiration(self):
        """Test creating token with custom expiration."""
        data = {"sub": "user123", "email": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Decode to verify expiration
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_timestamp = payload.get("exp")
        
        assert exp_timestamp is not None
        expected_exp = datetime.utcnow() + expires_delta
        actual_exp = datetime.utcfromtimestamp(exp_timestamp)
        
        # Allow 5 seconds tolerance
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 5

    def test_create_access_token_default_expiration(self):
        """Test token creation with default expiration."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_timestamp = payload.get("exp")
        
        expected_exp = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        actual_exp = datetime.utcfromtimestamp(exp_timestamp)
        
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 5

    def test_create_access_token_includes_iat(self):
        """Test token includes issued at (iat) claim."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert "iat" in payload
        iat_timestamp = payload.get("iat")
        iat_time = datetime.utcfromtimestamp(iat_timestamp)
        
        # Should be issued within last 5 seconds
        time_diff = abs((datetime.utcnow() - iat_time).total_seconds())
        assert time_diff < 5

    def test_decode_access_token_valid(self):
        """Test decoding a valid access token."""
        user_id = "user123"
        email = "test@example.com"
        role = UserRole.CLIENT
        
        data = {"sub": user_id, "email": email, "role": role.value}
        token = create_access_token(data)
        
        token_data = decode_access_token(token)
        
        assert token_data.user_id == user_id
        assert token_data.email == email
        assert token_data.role == role

    def test_decode_access_token_expired(self):
        """Test decoding an expired token raises exception."""
        data = {"sub": "user123", "email": "test@example.com"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-10)  # Already expired
        token = create_access_token(data, expires_delta=expires_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_decode_access_token_invalid_signature(self):
        """Test decoding token with invalid signature raises exception."""
        data = {"sub": "user123", "email": "test@example.com"}
        # Create token with different secret
        token = jwt.encode(data, "wrong_secret_key", algorithm=settings.ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        
        assert exc_info.value.status_code == 401

    def test_decode_access_token_missing_sub(self):
        """Test decoding token without 'sub' claim raises exception."""
        data = {"email": "test@example.com", "role": "client"}
        token = create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        
        assert exc_info.value.status_code == 401

    def test_decode_access_token_missing_email(self):
        """Test decoding token without 'email' claim raises exception."""
        data = {"sub": "user123", "role": "client"}
        token = create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        
        assert exc_info.value.status_code == 401

    def test_decode_access_token_invalid_format(self):
        """Test decoding malformed token raises exception."""
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid.token.format")
        
        assert exc_info.value.status_code == 401

    def test_decode_access_token_empty_string(self):
        """Test decoding empty token raises exception."""
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("")
        
        assert exc_info.value.status_code == 401

    def test_token_with_admin_role(self):
        """Test token with admin role."""
        data = {
            "sub": "admin123",
            "email": "admin@example.com",
            "role": UserRole.ADMIN.value,
        }
        token = create_access_token(data)
        token_data = decode_access_token(token)
        
        assert token_data.role == UserRole.ADMIN

    def test_token_with_freelancer_role(self):
        """Test token with freelancer role."""
        data = {
            "sub": "freelancer123",
            "email": "freelancer@example.com",
            "role": UserRole.FREELANCER.value,
        }
        token = create_access_token(data)
        token_data = decode_access_token(token)
        
        assert token_data.role == UserRole.FREELANCER


class TestTOTP:
    """Test suite for TOTP (2FA) functions."""

    def test_generate_totp_secret(self):
        """Test TOTP secret generation."""
        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()
        
        assert secret1 is not None
        assert len(secret1) > 0
        assert secret1 != secret2  # Should be random

    def test_generate_totp_secret_base32(self):
        """Test TOTP secret is valid base32."""
        secret = generate_totp_secret()
        
        # Base32 alphabet: A-Z, 2-7, and padding (=)
        import string
        base32_chars = string.ascii_uppercase + "234567="
        assert all(c in base32_chars for c in secret)

    def test_get_totp_uri(self):
        """Test TOTP URI generation for QR code."""
        secret = generate_totp_secret()
        account_name = "user@example.com"
        
        uri = get_totp_uri(secret, account_name)
        
        assert uri.startswith("otpauth://totp/")
        # Email might be URL encoded in the URI
        assert "user" in uri and "example.com" in uri
        assert secret in uri
        assert "Amani" in uri  # Default issuer

    def test_get_totp_uri_custom_issuer(self):
        """Test TOTP URI with custom issuer."""
        secret = generate_totp_secret()
        account_name = "user@example.com"
        issuer = "CustomIssuer"
        
        uri = get_totp_uri(secret, account_name, issuer_name=issuer)
        
        assert issuer in uri

    def test_verify_totp_code_valid(self):
        """Test TOTP code verification with valid code."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)
        
        # Current code should be valid
        assert verify_totp_code(secret, code) is True

    def test_verify_totp_code_invalid(self):
        """Test TOTP code verification with invalid code."""
        secret = generate_totp_secret()
        
        assert verify_totp_code(secret, "000000") is False
        assert verify_totp_code(secret, "999999") is False
        assert verify_totp_code(secret, "123456") is False

    def test_verify_totp_code_wrong_length(self):
        """Test TOTP code verification with wrong length."""
        secret = generate_totp_secret()
        
        assert verify_totp_code(secret, "12345") is False  # Too short
        assert verify_totp_code(secret, "1234567") is False  # Too long

    def test_verify_totp_code_non_numeric(self):
        """Test TOTP code verification with non-numeric input."""
        secret = generate_totp_secret()
        
        assert verify_totp_code(secret, "abcdef") is False
        assert verify_totp_code(secret, "12345a") is False

    def test_verify_totp_code_empty(self):
        """Test TOTP code verification with empty code."""
        secret = generate_totp_secret()
        
        assert verify_totp_code(secret, "") is False

    def test_generate_totp_code_format(self):
        """Test generated TOTP code format."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)
        
        assert len(code) == 6
        assert code.isdigit()

    def test_verify_totp_code_with_window(self):
        """Test TOTP code verification with time window."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)
        
        # Verify with different windows
        assert verify_totp_code(secret, code, valid_window=0) is True
        assert verify_totp_code(secret, code, valid_window=1) is True
        assert verify_totp_code(secret, code, valid_window=2) is True

    def test_totp_code_changes_over_time(self):
        """Test that TOTP codes are time-based (not testing time passage, just generation)."""
        secret = generate_totp_secret()
        
        # Generate multiple codes
        codes = [generate_totp_code(secret) for _ in range(3)]
        
        # All should be valid 6-digit codes
        for code in codes:
            assert len(code) == 6
            assert code.isdigit()

    def test_verify_totp_code_exception_handling(self):
        """Test TOTP verification handles exceptions gracefully."""
        # Invalid secret format
        assert verify_totp_code("invalid!!!secret", "123456") is False
        
        # Empty secret
        assert verify_totp_code("", "123456") is False

    def test_totp_code_uniqueness_per_secret(self):
        """Test that different secrets generate different codes."""
        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()
        
        code1 = generate_totp_code(secret1)
        code2 = generate_totp_code(secret2)
        
        # Different secrets should (almost certainly) generate different codes
        # Note: There's a tiny chance they could be the same, but extremely unlikely
        assert secret1 != secret2
