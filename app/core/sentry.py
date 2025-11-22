"""
Sentry error tracking integration.
"""

import logging
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_sentry():
    """
    Initialize Sentry error tracking.
    
    Sentry must be initialized before the application starts to capture errors.
    Requires SENTRY_DSN environment variable to be set.
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, error tracking disabled")
        return

    # Configure logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors and above as events
    )

    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
            # Enable performance monitoring
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            # Enable profiling
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                sentry_logging,
            ],
            # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
            # Adjust in production based on traffic volume
            # Additional options
            send_default_pii=False,  # Don't send personally identifiable information
            attach_stacktrace=True,  # Attach stack traces to messages
            # Custom tag for filtering
            before_send=before_send_handler,
        )
        logger.info(
            f"Sentry initialized successfully for environment: {settings.ENVIRONMENT}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_handler(event, hint):
    """
    Process events before sending to Sentry.
    
    Can be used to:
    - Filter out specific errors
    - Scrub sensitive data
    - Add custom tags or context
    """
    # Add custom tags
    if "tags" not in event:
        event["tags"] = {}
    
    event["tags"]["app_version"] = settings.APP_VERSION
    event["tags"]["environment"] = settings.ENVIRONMENT
    
    # Filter out health check errors if needed
    if "request" in event and event["request"].get("url", "").endswith("/health"):
        return None  # Don't send health check errors
    
    return event


def capture_exception(
    exception: Exception, 
    context: Optional[dict] = None,
    user_info: Optional[dict] = None,
) -> Optional[str]:
    """
    Manually capture an exception with optional context.
    
    Args:
        exception: The exception to capture
        context: Additional context dictionary
        user_info: User information dictionary (id, email, etc.)
        
    Returns:
        Event ID if sent to Sentry, None otherwise
    """
    if not settings.SENTRY_DSN:
        return None
    
    with sentry_sdk.push_scope() as scope:
        # Add context
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        # Add user info
        if user_info:
            scope.set_user(user_info)
        
        # Capture the exception
        event_id = sentry_sdk.capture_exception(exception)
        return event_id


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: Optional[dict] = None):
    """
    Add a breadcrumb to the current scope.
    
    Breadcrumbs are a trail of events that led up to an error.
    
    Args:
        message: Breadcrumb message
        category: Breadcrumb category (e.g., 'auth', 'db', 'payment')
        level: Log level (debug, info, warning, error, critical)
        data: Additional data dictionary
    """
    if not settings.SENTRY_DSN:
        return
    
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )
