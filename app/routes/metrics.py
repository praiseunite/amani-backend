"""
Metrics endpoint for Prometheus scraping.
"""

from fastapi import APIRouter, Response
from fastapi import status

from app.core.metrics import get_metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping.
    """
    return Response(content=get_metrics(), media_type="text/plain")
