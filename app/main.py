"""
Main FastAPI application for Amani Escrow Backend.
Security-first design with async support and structured logging.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import HTTPSRedirectMiddleware
from app.core.database import init_db
from app.core.rate_limit import RateLimitMiddleware
from app.core.exceptions import register_exception_handlers
from app.routes import health, auth, projects, milestones, escrow, kyc, wallet, payment

# Initialize logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Amani Escrow Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Amani Escrow Backend...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Secure escrow backend for Amani platform with FinCra integration",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Register exception handlers
register_exception_handlers(app)

# CORS Middleware - Configure allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTPS Enforcement Middleware
app.add_middleware(HTTPSRedirectMiddleware)

# Rate Limiting Middleware
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
        burst_size=settings.RATE_LIMIT_BURST_SIZE,
        exempt_paths=["/docs", "/redoc", "/openapi.json", "/api/v1/health", "/api/v1/ping"],
        redis_url=settings.REDIS_URL if settings.REDIS_ENABLED else None,
    )

# Trusted Host Middleware (prevent host header attacks)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.amani.com", "amani.com"],  # Update with actual domains
    )

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(milestones.router, prefix="/api/v1")
app.include_router(escrow.router, prefix="/api/v1")
app.include_router(kyc.router, prefix="/api/v1")
app.include_router(wallet.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")


# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests for audit purposes."""
    logger.info(
        f"Incoming request",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
        },
    )

    response = await call_next(request)

    logger.info(
        f"Request completed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
        },
    )

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
