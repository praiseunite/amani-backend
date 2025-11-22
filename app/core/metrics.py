"""
Prometheus metrics integration for application monitoring.
"""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from time import time

from app.core.config import settings

# Application info
app_info = Info("amani_app", "Application information")
app_info.info(
    {
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "app_name": settings.APP_NAME,
    }
)

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Database metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# Business metrics
escrow_transactions_total = Counter(
    "escrow_transactions_total",
    "Total escrow transactions",
    ["type", "status"],
)

user_registrations_total = Counter(
    "user_registrations_total",
    "Total user registrations",
)

kyc_submissions_total = Counter(
    "kyc_submissions_total",
    "Total KYC submissions",
    ["status"],
)

# Error metrics
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for HTTP requests.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and collect metrics.
        """
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path

        # Normalize path to avoid cardinality explosion
        endpoint = self._normalize_path(path)

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Track request duration
        start_time = time()

        try:
            response = await call_next(request)
            status = response.status_code

            # Record metrics
            http_requests_total.labels(
                method=method, endpoint=endpoint, status=status
            ).inc()

            duration = time() - start_time
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

            return response

        except Exception as e:
            # Record error
            errors_total.labels(
                error_type=type(e).__name__, endpoint=endpoint
            ).inc()
            raise

        finally:
            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

    def _normalize_path(self, path: str) -> str:
        """
        Normalize URL paths to reduce cardinality.
        Replace IDs and UUIDs with placeholders.
        """
        # Split path into segments
        segments = path.strip("/").split("/")

        normalized_segments = []
        for segment in segments:
            # Replace UUIDs and numeric IDs
            if self._is_uuid_or_id(segment):
                normalized_segments.append("{id}")
            else:
                normalized_segments.append(segment)

        return "/" + "/".join(normalized_segments)

    def _is_uuid_or_id(self, segment: str) -> bool:
        """
        Check if a segment looks like an ID or UUID.
        """
        # Check if it's all digits (numeric ID)
        if segment.isdigit():
            return True

        # Check if it looks like a UUID (contains hyphens and hex characters)
        if "-" in segment and len(segment) > 20:
            parts = segment.split("-")
            if all(all(c in "0123456789abcdefABCDEF" for c in part) for part in parts):
                return True

        return False


def get_metrics():
    """
    Get Prometheus metrics in text format.
    """
    return generate_latest()
