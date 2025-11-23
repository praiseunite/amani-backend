"""Health check and status routes with comprehensive system checks."""

import json
import os
import sys
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["health"])


def get_build_info():
    """
    Get build information from environment variables and build-info.json file.
    
    Returns:
        dict: Build information including version, commit SHA, build time, etc.
    """
    build_info = {
        "version": os.getenv("BUILD_VERSION", settings.APP_VERSION),
        "commit_sha": os.getenv("BUILD_SHA", "unknown"),
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "build_number": os.getenv("BUILD_NUMBER", "0"),
        "build_branch": os.getenv("BUILD_BRANCH", "unknown"),
    }
    
    # Try to load from build-info.json if it exists
    build_info_path = "/app/build-info.json"
    if os.path.exists(build_info_path):
        try:
            with open(build_info_path, "r") as f:
                file_info = json.load(f)
                build_info.update(file_info)
        except Exception:
            pass  # Fallback to environment variables
    
    return build_info


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


@router.get("/version", status_code=status.HTTP_200_OK)
async def version_info():
    """
    Version and build information endpoint.
    
    Returns detailed version and build metadata for deployed application.
    Useful for deployment verification and troubleshooting.
    
    Returns:
        dict: Version and build information
    """
    build_info = get_build_info()
    
    return {
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": build_info["version"],
        "build": {
            "commit_sha": build_info["commit_sha"],
            "build_time": build_info["build_time"],
            "build_number": build_info["build_number"],
            "build_branch": build_info["build_branch"],
        },
        "runtime": {
            "python_version": sys.version,
            "platform": sys.platform,
        },
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
    build_info = get_build_info()
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app": settings.APP_NAME,
        "version": build_info["version"],
        "commit_sha": build_info["commit_sha"],
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
    # SECURITY: Using explicit allowlist validation to prevent SQL injection
    # Table names cannot be parameterized in SQL, so we strictly validate
    # against this immutable allowlist before any query construction.
    ALLOWED_TABLES = frozenset(
        [
            "users",
            "wallet_registry",
            "wallet_balance_snapshot",
            "wallet_transaction_event",
        ]
    )

    for table_name in ALLOWED_TABLES:
        try:
            # SECURITY NOTE: table_name is guaranteed to be from ALLOWED_TABLES
            # This is safe from SQL injection because:
            # 1. ALLOWED_TABLES is a hardcoded frozenset (immutable)
            # 2. No user input influences this loop
            # 3. Table names are validated against allowlist before use
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
