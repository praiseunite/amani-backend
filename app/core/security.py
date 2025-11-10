"""
Security middleware for HTTPS enforcement, security headers, and KYC validation.
"""
from fastapi import Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy import select
from app.core.config import settings
from app.core.database import get_db
from app.models.kyc import Kyc, KycStatus
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


class KYCEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce KYC approval before allowing transaction operations.
    """
    
    # Routes that require KYC approval
    PROTECTED_TRANSACTION_ROUTES = [
        "/api/v1/escrow/hold",
        "/api/v1/escrow/release",
    ]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is a transaction route that requires KYC
        path = request.url.path
        
        # Only check POST requests to transaction routes
        if request.method == "POST" and any(path.startswith(route) for route in self.PROTECTED_TRANSACTION_ROUTES):
            # Get user from request state (set by authentication middleware)
            user = getattr(request.state, "user", None)
            
            if user is not None:
                # Check KYC status
                try:
                    # Get database session
                    db_gen = get_db()
                    db = await anext(db_gen)
                    
                    try:
                        # Query for approved KYC
                        stmt = select(Kyc).where(
                            Kyc.user_id == user.id,
                            Kyc.status == KycStatus.APPROVED
                        )
                        result = await db.execute(stmt)
                        kyc = result.scalar_one_or_none()
                        
                        if kyc is None:
                            logger.warning(f"User {user.id} attempted transaction without approved KYC")
                            return JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={
                                    "detail": "KYC approval required to perform transactions. Please complete KYC verification."
                                }
                            )
                    finally:
                        # Close the database session
                        await db.close()
                        
                except Exception as e:
                    logger.error(f"Error checking KYC status: {str(e)}")
                    # In case of error, allow the request to proceed
                    # The actual endpoint will handle authorization
        
        response = await call_next(request)
        return response

