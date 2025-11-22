"""
Configuration module for the Amani Escrow Backend.
Handles environment variables and application settings.
"""

from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Settings
    APP_NAME: str = "Amani Escrow Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database - PostgreSQL (Supabase)
    DATABASE_URL: str
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # FinCra API
    FINCRA_API_KEY: str = ""
    FINCRA_API_SECRET: str = ""
    FINCRA_BASE_URL: str = "https://api.fincra.com"

    # CORS Settings
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:3000"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # HTTPS Enforcement
    FORCE_HTTPS: bool = True

    # Redis Configuration (for rate limiting)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_SIZE: int = 100

    # Email Configuration (Brevo)
    BREVO_API_KEY: str = ""
    BREVO_FROM_EMAIL: str = ""
    BREVO_FROM_NAME: str = ""
    BREVO_SMTP_LOGIN: str = ""

    # Monitoring and Observability
    # Sentry Error Tracking
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1  # 10% of transactions

    # OpenTelemetry Tracing
    TRACING_ENABLED: bool = False
    TRACING_EXPORTER: str = "console"  # Options: otlp, console
    OTLP_ENDPOINT: str = "http://localhost:4317"
    OTLP_HEADERS: str = ""  # Comma-separated key=value pairs

    # Alerting and Notifications
    SLACK_WEBHOOK_URL: str = ""
    PAGERDUTY_API_KEY: str = ""
    PAGERDUTY_SERVICE_ID: str = ""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


# Create a global settings instance
settings = Settings()
