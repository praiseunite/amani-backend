"""
Comprehensive unit tests for app.core.config module.
Tests Settings class, field validators, and configuration loading.
"""

import pytest
import os
from pydantic import ValidationError
from app.core.config import Settings


class TestSettings:
    """Test suite for Settings configuration class."""

    def test_settings_initialization_with_defaults(self, monkeypatch):
        """Test Settings initialization with default values."""
        # Set required fields
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-123")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        settings = Settings()
        
        assert settings.APP_NAME == "Amani Escrow Backend"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is True
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_settings_missing_required_fields(self, monkeypatch):
        """Test Settings raises error when required fields are missing."""
        # Clear environment
        for key in ["SECRET_KEY", "DATABASE_URL"]:
            monkeypatch.delenv(key, raising=False)
        
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_secret_key_validation(self, monkeypatch):
        """Test SECRET_KEY is properly loaded."""
        secret_key = "my-super-secret-key-12345"
        monkeypatch.setenv("SECRET_KEY", secret_key)
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        
        settings = Settings()
        
        assert settings.SECRET_KEY == secret_key

    def test_settings_database_url_validation(self, monkeypatch):
        """Test DATABASE_URL is properly loaded."""
        db_url = "postgresql+asyncpg://user:pass@localhost:5432/amani"
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", db_url)
        
        settings = Settings()
        
        assert settings.DATABASE_URL == db_url

    def test_settings_allowed_origins_string_parsing(self, monkeypatch):
        """Test ALLOWED_ORIGINS parsing from comma-separated string."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000,https://example.com,https://app.example.com")
        
        settings = Settings()
        
        assert isinstance(settings.ALLOWED_ORIGINS, list)
        assert len(settings.ALLOWED_ORIGINS) == 3
        assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
        assert "https://example.com" in settings.ALLOWED_ORIGINS
        assert "https://app.example.com" in settings.ALLOWED_ORIGINS

    def test_settings_allowed_origins_already_list(self, monkeypatch):
        """Test ALLOWED_ORIGINS when already a list."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        
        # When passed as list directly (programmatic usage)
        settings = Settings(
            SECRET_KEY="test-secret",
            DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
            ALLOWED_ORIGINS=["http://localhost:3000", "https://example.com"]
        )
        
        assert isinstance(settings.ALLOWED_ORIGINS, list)
        assert len(settings.ALLOWED_ORIGINS) == 2

    def test_settings_allowed_origins_with_spaces(self, monkeypatch):
        """Test ALLOWED_ORIGINS parsing with spaces."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("ALLOWED_ORIGINS", " http://localhost:3000 , https://example.com ")
        
        settings = Settings()
        
        # Should strip spaces
        assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
        assert "https://example.com" in settings.ALLOWED_ORIGINS

    def test_settings_redis_configuration(self, monkeypatch):
        """Test Redis configuration settings."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
        monkeypatch.setenv("REDIS_ENABLED", "true")
        
        settings = Settings()
        
        assert settings.REDIS_URL == "redis://localhost:6379/1"
        assert settings.REDIS_ENABLED is True

    def test_settings_rate_limit_configuration(self, monkeypatch):
        """Test rate limiting configuration."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
        monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "120")
        monkeypatch.setenv("RATE_LIMIT_BURST_SIZE", "200")
        
        settings = Settings()
        
        assert settings.RATE_LIMIT_ENABLED is False
        assert settings.RATE_LIMIT_PER_MINUTE == 120
        assert settings.RATE_LIMIT_BURST_SIZE == 200

    def test_settings_logging_configuration(self, monkeypatch):
        """Test logging configuration."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("LOG_FILE", "/var/log/amani/app.log")
        
        settings = Settings()
        
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.LOG_FILE == "/var/log/amani/app.log"

    def test_settings_https_enforcement(self, monkeypatch):
        """Test HTTPS enforcement setting."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("FORCE_HTTPS", "false")
        
        settings = Settings()
        
        assert settings.FORCE_HTTPS is False

    def test_settings_fincra_configuration(self, monkeypatch):
        """Test FinCra API configuration."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("FINCRA_API_KEY", "fincra-key-123")
        monkeypatch.setenv("FINCRA_API_SECRET", "fincra-secret-456")
        monkeypatch.setenv("FINCRA_BASE_URL", "https://sandbox.fincra.com")
        
        settings = Settings()
        
        assert settings.FINCRA_API_KEY == "fincra-key-123"
        assert settings.FINCRA_API_SECRET == "fincra-secret-456"
        assert settings.FINCRA_BASE_URL == "https://sandbox.fincra.com"

    def test_settings_email_configuration(self, monkeypatch):
        """Test email (Brevo) configuration."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("BREVO_API_KEY", "brevo-key-123")
        monkeypatch.setenv("BREVO_FROM_EMAIL", "noreply@amani.com")
        monkeypatch.setenv("BREVO_FROM_NAME", "Amani Support")
        monkeypatch.setenv("BREVO_SMTP_LOGIN", "smtp-login")
        
        settings = Settings()
        
        assert settings.BREVO_API_KEY == "brevo-key-123"
        assert settings.BREVO_FROM_EMAIL == "noreply@amani.com"
        assert settings.BREVO_FROM_NAME == "Amani Support"
        assert settings.BREVO_SMTP_LOGIN == "smtp-login"

    def test_settings_supabase_configuration(self, monkeypatch):
        """Test Supabase configuration."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "supabase-key")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "supabase-service-key")
        
        settings = Settings()
        
        assert settings.SUPABASE_URL == "https://project.supabase.co"
        assert settings.SUPABASE_KEY == "supabase-key"
        assert settings.SUPABASE_SERVICE_KEY == "supabase-service-key"

    def test_settings_environment_variations(self, monkeypatch):
        """Test different environment configurations."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        
        # Test production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        settings_prod = Settings()
        assert settings_prod.ENVIRONMENT == "production"
        
        # Test staging environment
        monkeypatch.setenv("ENVIRONMENT", "staging")
        settings_staging = Settings()
        assert settings_staging.ENVIRONMENT == "staging"
        
        # Test development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        settings_dev = Settings()
        assert settings_dev.ENVIRONMENT == "development"

    def test_settings_debug_mode(self, monkeypatch):
        """Test DEBUG mode configuration."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("DEBUG", "false")
        
        settings = Settings()
        
        assert settings.DEBUG is False

    def test_settings_host_and_port(self, monkeypatch):
        """Test HOST and PORT configuration."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("HOST", "127.0.0.1")
        monkeypatch.setenv("PORT", "9000")
        
        settings = Settings()
        
        assert settings.HOST == "127.0.0.1"
        assert settings.PORT == 9000

    def test_settings_token_expiration(self, monkeypatch):
        """Test access token expiration configuration."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        
        settings = Settings()
        
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    def test_settings_algorithm(self, monkeypatch):
        """Test JWT algorithm configuration."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("ALGORITHM", "RS256")
        
        settings = Settings()
        
        assert settings.ALGORITHM == "RS256"
