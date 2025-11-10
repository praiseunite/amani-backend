"""
Health check and status routes.
"""
from fastapi import APIRouter, status
from datetime import datetime
from app.core.config import settings

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
        "environment": settings.ENVIRONMENT
    }


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    """
    Simple ping endpoint.
    
    Returns:
        dict: Pong response
    """
    return {"message": "pong"}
