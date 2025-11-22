"""
OpenTelemetry integration for distributed tracing.
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_tracing(app=None):
    """
    Initialize OpenTelemetry tracing.
    
    Supports multiple exporters:
    - OTLP (for cloud providers like DataDog, Honeycomb, Jaeger, etc.)
    - Console (for debugging)
    
    Args:
        app: Optional FastAPI application instance to instrument
    """
    if not settings.TRACING_ENABLED:
        logger.info("Tracing is disabled")
        return None

    # Create resource with service information
    resource = Resource(
        attributes={
            SERVICE_NAME: settings.APP_NAME,
            SERVICE_VERSION: settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add exporters based on configuration
    if settings.TRACING_EXPORTER == "otlp":
        _add_otlp_exporter(provider)
    elif settings.TRACING_EXPORTER == "console":
        _add_console_exporter(provider)
    else:
        # Default to console in development, but warn in production
        if settings.ENVIRONMENT == "production":
            logger.error(
                f"Invalid tracing exporter '{settings.TRACING_EXPORTER}' in production. "
                "Valid options: otlp, console. Tracing disabled."
            )
            return None
        else:
            logger.warning(
                f"Unknown tracing exporter: {settings.TRACING_EXPORTER}, defaulting to console"
            )
            _add_console_exporter(provider)

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    # Instrument libraries
    _instrument_libraries()

    # Instrument FastAPI if app is provided
    if app:
        FastAPIInstrumentor.instrument_app(app)

    logger.info(
        f"Tracing initialized with {settings.TRACING_EXPORTER} exporter"
    )

    return trace.get_tracer(__name__)


def _add_otlp_exporter(provider: TracerProvider):
    """Add OTLP exporter to tracer provider."""
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTLP_ENDPOINT,
        headers=_get_otlp_headers(),
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    logger.info(f"OTLP exporter configured at {settings.OTLP_ENDPOINT}")


def _add_console_exporter(provider: TracerProvider):
    """Add console exporter to tracer provider (for debugging)."""
    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(console_exporter))
    logger.info("Console exporter configured")


def _get_otlp_headers() -> Optional[dict]:
    """
    Get headers for OTLP exporter.
    
    Used for authentication with cloud providers.
    """
    if settings.OTLP_HEADERS:
        # Parse headers from comma-separated key=value pairs
        headers = {}
        for pair in settings.OTLP_HEADERS.split(","):
            if "=" in pair:
                key, value = pair.strip().split("=", 1)
                headers[key.strip()] = value.strip()
        return headers
    return None


def _instrument_libraries():
    """Instrument common libraries for automatic tracing."""
    try:
        # SQLAlchemy instrumentation
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")

    try:
        # HTTPX client instrumentation
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument HTTPX: {e}")


def get_tracer(name: str = __name__):
    """
    Get a tracer instance.
    
    Args:
        name: Name for the tracer (usually __name__)
        
    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def add_span_attributes(**attributes):
    """
    Add attributes to the current span.
    
    Useful for adding custom metadata to traces.
    """
    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def record_exception(exception: Exception):
    """
    Record an exception in the current span.
    
    Args:
        exception: The exception to record
    """
    current_span = trace.get_current_span()
    if current_span:
        current_span.record_exception(exception)
