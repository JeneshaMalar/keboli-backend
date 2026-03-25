"""System log routes for persisting structured log entries from external services."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db
from src.core.exceptions import AppError
from src.data.models.system_log import SystemLog
from src.observability.logging.logger import logger
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
) -> SystemLog:
    """Create a new system log entry.

    Args:
        log_data: Structured log data to persist.
        db: Async database session.

    Returns:
        The persisted log entry.

    Raises:
        AppError: If the log entry cannot be created.
    """
    try:
        log_dict = log_data.model_dump()

        uuid_fields = [
            "session_id",
            "candidate_id",
            "assessment_id",
            "user_id",
            "request_id",
        ]

        if log_dict.get("details") is None:
            log_dict["details"] = {}

        for field in uuid_fields:
            val = log_dict.get(field)
            if val:
                try:
                    if not isinstance(val, uuid.UUID):
                        log_dict[field] = uuid.UUID(str(val))
                except (ValueError, TypeError):
                    log_dict["details"][f"original_{field}"] = str(val)
                    log_dict[field] = None

        new_log = SystemLog(**log_dict)
        db.add(new_log)
        await db.commit()
        await db.refresh(new_log)
        return new_log
    except Exception as e:
        logger.error("failed_to_create_log_entry", error=str(e))
        raise AppError(
            message=f"Failed to create log entry: {e!s}",
            status_code=500,
            error_code="LOG_CREATION_FAILED",
        ) from e
