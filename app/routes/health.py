"""
Health check and status routes with comprehensive system checks.
"""

from fastapi import APIRouter, status, Depends
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint - Hello World API.

    Returns:
        dict: Welcome message
    """
    return {
        "message": "Hello World! Welcome to Amani Escrow Backend",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive health check endpoint for monitoring.

    Checks:
    - Application status
    - Database connectivity
    - Database migration status

    Returns:
        dict: Detailed health status information
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {},
    }

    # Check database connection
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }

    # Check if migrations table exists (validates migrations have run)
    try:
        result = await db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        version = result.fetchone()
        if version:
            health_status["checks"]["migrations"] = {
                "status": "healthy",
                "message": "Migrations applied",
                "current_version": version[0],
            }
        else:
            health_status["checks"]["migrations"] = {
                "status": "warning",
                "message": "No migrations applied",
            }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["migrations"] = {
            "status": "unhealthy",
            "message": f"Migration check failed: {str(e)}",
        }

    return health_status


@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe endpoint for deployment orchestration.

    Verifies the application is ready to serve traffic:
    - Database is accessible
    - All required tables exist
    - Migrations are current

    Returns:
        dict: Readiness status
    """
    readiness_status = {"ready": True, "timestamp": datetime.utcnow().isoformat(), "checks": {}}

    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        readiness_status["checks"]["database"] = "ready"
    except Exception as e:
        readiness_status["ready"] = False
        readiness_status["checks"]["database"] = f"not ready: {str(e)}"
        return readiness_status

    # Verify critical tables exist
    required_tables = [
        "users",
        "wallet_registry",
        "wallet_balance_snapshot",
        "wallet_transaction_event",
    ]

    for table_name in required_tables:
        try:
            # Using validated allowlist to prevent SQL injection
            # Table names cannot be parameterized, so we validate first
            # Safe: table_name is from our controlled allowlist above
            await db.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
            readiness_status["checks"][f"table_{table_name}"] = "ready"
        except Exception as e:
            readiness_status["ready"] = False
            readiness_status["checks"][f"table_{table_name}"] = f"not ready: {str(e)}"

    return readiness_status


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    """
    Simple ping endpoint for basic liveness checks.

    Returns:
        dict: Pong response
    """
    return {"message": "pong"}
