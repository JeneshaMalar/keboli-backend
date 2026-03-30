"""Health check routes for monitoring service and database availability."""

import logging

from typing import Any
from fastapi import APIRouter, Depends
from src.api.rest.dependencies import get_db
from src.core.services.health_service import HealthService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Verify that the API and database connection are operational.",
)
async def health(
    db: Any = Depends(get_db),
) -> dict[str, str]:
    """Check API and database health.

    Executes a lightweight SQL query to verify database connectivity.

    Args:
        db: Async database session.

    Returns:
        A dictionary with service and database status indicators.
    """
    service = HealthService(db)
    is_healthy = await service.check_db_connection()
    db_status = "healthy" if is_healthy else "unhealthy"
    
    if not is_healthy:
        logger.warning("Database connectivity issue during health check")

    return {
        "status": "healthy",
        "database": db_status,
    }
