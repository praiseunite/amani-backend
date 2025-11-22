"""
Pytest configuration and fixtures.
"""

import os

import pytest

# Set test environment variables before any imports
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-testing-12345678901234567890")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("REDIS_ENABLED", "false")


@pytest.fixture
def mock_settings():
    """Fixture to provide test settings."""
    return {
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
        "ENVIRONMENT": "testing",
    }
