"""Health check endpoints for liveness and readiness probes."""

import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db

router = APIRouter()


class ServiceStatus(BaseModel):
    """Status of an individual backing service."""

    database: str = "unknown"


class HealthResponse(BaseModel):
    """Structured health-check response returned by the /health endpoint."""

    status: str = "ok"
    services: ServiceStatus = ServiceStatus()
    response_time_ms: float = 0.0
    error: str | None = None


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application health check",
    description="Returns the health status of the application and its backing services.",
)
async def health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check application and database connectivity.

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        HealthResponse with service statuses and response time.
    """
    start = time.time()

    health_status = HealthResponse()

    try:
        await db.execute(text("SELECT 1"))
        health_status.services.database = "connected"
    except Exception as e:
        health_status.status = "degraded"
        health_status.services.database = "disconnected"
        health_status.error = str(e)

    health_status.response_time_ms = round((time.time() - start) * 1000, 2)

    return health_status
