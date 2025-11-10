"""
Security middleware for HTTPS enforcement and security headers.
"""
from fastapi import Request, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS connections in production.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.force_https = settings.FORCE_HTTPS and settings.ENVIRONMENT == "production"
    
    async def dispatch(self, request: Request, call_next):
        # Enforce HTTPS in production
        if self.force_https:
            # Check if request is not secure
            if request.url.scheme != "https":
                # Check for X-Forwarded-Proto header (common in reverse proxies)
                forwarded_proto = request.headers.get("X-Forwarded-Proto")
                if forwarded_proto != "https":
                    # Redirect to HTTPS
                    url = request.url.replace(scheme="https")
                    logger.warning(f"Redirecting HTTP request to HTTPS: {url}")
                    return RedirectResponse(url=str(url), status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
