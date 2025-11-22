"""
Unit tests for authentication utilities.
"""

import pytest
from datetime import timedelta
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from app.models.user import UserRole
from fastapi import HTTPException


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "Test1234"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "Test1234"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test verifying wrong password."""
        password = "Test1234"
        wrong_password = "Wrong1234"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_token(self):
        """Test creating JWT token."""
        data = {"sub": "user123", "email": "test@example.com", "role": "client"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_token_with_expiry(self):
        """Test creating JWT token with custom expiry."""
        data = {"sub": "user123", "email": "test@example.com", "role": "client"}
        token = create_access_token(data, expires_delta=timedelta(minutes=60))
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        """Test decoding valid JWT token."""
        data = {"sub": "user123", "email": "test@example.com", "role": "client"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded.user_id == "user123"
        assert decoded.email == "test@example.com"
        assert decoded.role == UserRole.CLIENT

    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token."""
        with pytest.raises(HTTPException) as exc:
            decode_access_token("invalid_token")
        assert exc.value.status_code == 401

    def test_decode_token_with_admin_role(self):
        """Test decoding JWT token with admin role."""
        data = {"sub": "admin123", "email": "admin@example.com", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded.role == UserRole.ADMIN

    def test_decode_token_with_freelancer_role(self):
        """Test decoding JWT token with freelancer role."""
        data = {"sub": "freelancer123", "email": "freelancer@example.com", "role": "freelancer"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded.role == UserRole.FREELANCER
