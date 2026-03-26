"""System log routes for persisting structured log entries from external services."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db
from src.core.services.log_service import LogService
from src.schemas.system_log_schema import LogCreate, LogResponse

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post(
    "/",
    response_model=LogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a system log entry",
    description="Persist a structured log entry from an external service (e.g., interview agent).",
)
async def create_log(
    log_data: LogCreate,
    db: AsyncSession = Depends(get_db),
) -> LogResponse:
    """Create a new system log entry.

    Args:
        log_data: Structured log data to persist.
        db: Async database session.

    Returns:
        The persisted log entry.

    Raises:
        AppError: If the log entry cannot be created.
    """
    service = LogService(db)
    new_log = await service.create_log(log_data.model_dump())
    return LogResponse.model_validate(new_log)
