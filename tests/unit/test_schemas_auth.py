"""
Comprehensive unit tests for Pydantic schemas.
Tests validation, serialization, and business rules.
"""

import pytest
from pydantic import ValidationError
from app.schemas.auth import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    TokenData,
    Token,
    UserUpdate,
    PasswordChange,
    MagicLinkRequest,
    VerifyOtpRequest,
)
from app.models.user import UserRole


class TestUserBase:
    """Test suite for UserBase schema."""

    def test_user_base_valid_data(self):
        """Test UserBase with valid data."""
        user = UserBase(
            email="test@example.com",
            full_name="John Doe",
            phone_number="+1234567890",
            role=UserRole.CLIENT,
        )
        
        assert user.email == "test@example.com"
        assert user.full_name == "John Doe"
        assert user.phone_number == "+1234567890"
        assert user.role == UserRole.CLIENT

    def test_user_base_minimal_data(self):
        """Test UserBase with minimal required data."""
        user = UserBase(email="minimal@example.com")
        
        assert user.email == "minimal@example.com"
        assert user.full_name is None
        assert user.phone_number is None
        assert user.role == UserRole.CLIENT  # default

    def test_user_base_invalid_email(self):
        """Test UserBase with invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email="invalid-email")
        
        errors = exc_info.value.errors()
        assert any("email" in str(e) for e in errors)

    def test_user_base_different_roles(self):
        """Test UserBase with different roles."""
        client = UserBase(email="client@example.com", role=UserRole.CLIENT)
        freelancer = UserBase(email="freelancer@example.com", role=UserRole.FREELANCER)
        admin = UserBase(email="admin@example.com", role=UserRole.ADMIN)
        
        assert client.role == UserRole.CLIENT
        assert freelancer.role == UserRole.FREELANCER
        assert admin.role == UserRole.ADMIN


class TestUserCreate:
    """Test suite for UserCreate schema."""

    def test_user_create_valid_password(self):
        """Test UserCreate with valid password."""
        user = UserCreate(
            email="test@example.com",
            password="ValidPass123",
            full_name="Test User",
        )
        
        assert user.password == "ValidPass123"

    def test_user_create_password_too_short(self):
        """Test UserCreate with password too short."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="Short1")
        
        errors = exc_info.value.errors()
        assert any("at least 8 characters" in str(e) for e in errors)

    def test_user_create_password_no_uppercase(self):
        """Test UserCreate with password lacking uppercase."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="nouppercase123")
        
        errors = exc_info.value.errors()
        assert any("uppercase" in str(e).lower() for e in errors)

    def test_user_create_password_no_lowercase(self):
        """Test UserCreate with password lacking lowercase."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="NOLOWERCASE123")
        
        errors = exc_info.value.errors()
        assert any("lowercase" in str(e).lower() for e in errors)

    def test_user_create_password_no_digit(self):
        """Test UserCreate with password lacking digits."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="NoDigitsHere")
        
        errors = exc_info.value.errors()
        assert any("digit" in str(e).lower() for e in errors)

    def test_user_create_strong_password(self):
        """Test UserCreate with strong password."""
        passwords = [
            "StrongPass123!",
            "MyP@ssw0rd",
            "Secure123",
            "ValidPassword1",
        ]
        
        for password in passwords:
            user = UserCreate(email="test@example.com", password=password)
            assert user.password == password

    def test_user_create_inherits_from_user_base(self):
        """Test that UserCreate includes UserBase fields."""
        user = UserCreate(
            email="test@example.com",
            password="ValidPass123",
            full_name="Test User",
            phone_number="+1234567890",
            role=UserRole.FREELANCER,
        )
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.phone_number == "+1234567890"
        assert user.role == UserRole.FREELANCER


class TestUserLogin:
    """Test suite for UserLogin schema."""

    def test_user_login_valid(self):
        """Test UserLogin with valid data."""
        login = UserLogin(email="user@example.com", password="password123")
        
        assert login.email == "user@example.com"
        assert login.password == "password123"

    def test_user_login_invalid_email(self):
        """Test UserLogin with invalid email."""
        with pytest.raises(ValidationError):
            UserLogin(email="not-an-email", password="password")

    def test_user_login_missing_fields(self):
        """Test UserLogin with missing required fields."""
        with pytest.raises(ValidationError):
            UserLogin(email="test@example.com")
        
        with pytest.raises(ValidationError):
            UserLogin(password="password")


class TestTokenData:
    """Test suite for TokenData schema."""

    def test_token_data_creation(self):
        """Test TokenData creation."""
        from uuid import uuid4
        
        user_id = str(uuid4())
        token_data = TokenData(
            user_id=user_id,
            email="test@example.com",
            role=UserRole.CLIENT,
        )
        
        assert token_data.user_id == user_id
        assert token_data.email == "test@example.com"
        assert token_data.role == UserRole.CLIENT

    def test_token_data_different_roles(self):
        """Test TokenData with different roles."""
        from uuid import uuid4
        
        user_id = str(uuid4())
        
        client = TokenData(user_id=user_id, email="c@example.com", role=UserRole.CLIENT)
        admin = TokenData(user_id=user_id, email="a@example.com", role=UserRole.ADMIN)
        
        assert client.role == UserRole.CLIENT
        assert admin.role == UserRole.ADMIN


class TestToken:
    """Test suite for Token schema."""

    def test_token_creation(self):
        """Test Token schema creation."""
        from datetime import datetime
        from uuid import uuid4
        
        user = UserResponse(
            id=uuid4(),
            email="test@example.com",
            role=UserRole.CLIENT,
            is_active=True,
            is_verified=False,
            is_superuser=False,
            created_at=datetime.utcnow(),
        )
        
        token = Token(
            access_token="jwt_token_here",
            token_type="bearer",
            expires_in=3600,
            user=user,
        )
        
        assert token.access_token == "jwt_token_here"
        assert token.token_type == "bearer"
        assert token.expires_in == 3600

    def test_token_default_type(self):
        """Test Token default token type."""
        from datetime import datetime
        from uuid import uuid4
        
        user = UserResponse(
            id=uuid4(),
            email="test@example.com",
            role=UserRole.CLIENT,
            is_active=True,
            is_verified=False,
            is_superuser=False,
            created_at=datetime.utcnow(),
        )
        
        token = Token(access_token="jwt_token", expires_in=3600, user=user)
        
        assert token.token_type == "bearer"


class TestPasswordChange:
    """Test suite for PasswordChange schema."""

    def test_password_change_valid(self):
        """Test PasswordChange with valid data."""
        change = PasswordChange(
            current_password="OldPass123",
            new_password="NewPass456",
        )
        
        assert change.current_password == "OldPass123"
        assert change.new_password == "NewPass456"

    def test_password_change_new_password_validation(self):
        """Test new password validation."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(
                current_password="OldPass123",
                new_password="weak",
            )
        
        errors = exc_info.value.errors()
        assert any("at least 8 characters" in str(e) for e in errors)


class TestMagicLinkRequest:
    """Test suite for MagicLinkRequest schema."""

    def test_magic_link_request_valid(self):
        """Test MagicLinkRequest with valid email."""
        request = MagicLinkRequest(email="user@example.com")
        
        assert request.email == "user@example.com"

    def test_magic_link_request_invalid_email(self):
        """Test MagicLinkRequest with invalid email."""
        with pytest.raises(ValidationError):
            MagicLinkRequest(email="not-an-email")


class TestVerifyOtpRequest:
    """Test suite for VerifyOtpRequest schema."""

    def test_verify_otp_request_valid(self):
        """Test VerifyOtpRequest with valid OTP."""
        request = VerifyOtpRequest(email="user@example.com", otp="123456")
        
        assert request.email == "user@example.com"
        assert request.otp == "123456"

    def test_verify_otp_request_invalid_length(self):
        """Test VerifyOtpRequest with invalid OTP length."""
        with pytest.raises(ValidationError):
            VerifyOtpRequest(email="user@example.com", otp="12345")  # Too short
        
        with pytest.raises(ValidationError):
            VerifyOtpRequest(email="user@example.com", otp="1234567")  # Too long


class TestUserUpdate:
    """Test suite for UserUpdate schema."""

    def test_user_update_all_fields(self):
        """Test UserUpdate with all fields."""
        update = UserUpdate(
            full_name="Updated Name",
            phone_number="+1234567890",
            avatar_url="https://example.com/avatar.jpg",
            bio="Updated bio",
        )
        
        assert update.full_name == "Updated Name"
        assert update.phone_number == "+1234567890"
        assert update.avatar_url == "https://example.com/avatar.jpg"
        assert update.bio == "Updated bio"

    def test_user_update_partial_fields(self):
        """Test UserUpdate with partial fields."""
        update = UserUpdate(full_name="New Name")
        
        assert update.full_name == "New Name"
        assert update.phone_number is None
        assert update.avatar_url is None
        assert update.bio is None


class TestSchemaValidation:
    """Test suite for cross-schema validation scenarios."""

    def test_user_create_to_dict(self):
        """Test serialization of UserCreate."""
        user = UserCreate(
            email="test@example.com",
            password="ValidPass123",
            full_name="Test User",
        )
        
        data = user.model_dump()
        
        assert "email" in data
        assert "password" in data
        assert "full_name" in data

    def test_token_data_serialization(self):
        """Test TokenData serialization."""
        from uuid import uuid4
        
        token_data = TokenData(
            user_id=str(uuid4()),
            email="test@example.com",
            role=UserRole.CLIENT,
        )
        
        data = token_data.model_dump()
        
        assert "user_id" in data
        assert "email" in data
        assert "role" in data

    def test_user_login_json(self):
        """Test UserLogin JSON serialization."""
        login = UserLogin(email="test@example.com", password="password123")
        
        json_str = login.model_dump_json()
        
        assert "test@example.com" in json_str
        assert "password123" in json_str

    def test_password_field_description(self):
        """Test UserCreate password field has description."""
        schema = UserCreate.model_json_schema()
        
        assert "password" in schema["properties"]
        # Check that field has constraints
        password_field = schema["properties"]["password"]
        assert "minLength" in password_field or "description" in password_field
