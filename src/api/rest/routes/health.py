"""Health check routes for monitoring service and database availability."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Verify that the API and database connection are operational.",
)
async def health(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Check API and database health.

    Executes a lightweight SQL query to verify database connectivity.

    Args:
        db: Async database session.

    Returns:
        A dictionary with service and database status indicators.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except ConnectionRefusedError:
        logger.warning("Database connection refused during health check")
        db_status = "unhealthy"
    except OSError as e:
        logger.warning("Database connectivity issue during health check: %s", e)
        db_status = "unhealthy"

    return {
        "status": "healthy",
        "database": db_status,
    }
