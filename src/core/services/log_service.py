"""System log service for persisting structured log entries."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AppError
from src.data.models.system_log import SystemLog

logger = logging.getLogger(__name__)


class LogService:
    """Service layer for persisting structured system log entries.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_log(self, log_data: dict[str, object]) -> SystemLog:
        """Create and persist a structured system log entry.

        Performs UUID validation and conversion for known ID fields,
        preserving originals in the details dict on failure.

        Args:
            log_data: Dictionary of log entry fields from the request.

        Returns:
            The persisted SystemLog instance.

        Raises:
            AppError: If the log entry cannot be created.
        """
        try:
            uuid_fields = [
                "session_id",
                "candidate_id",
                "assessment_id",
                "user_id",
                "request_id",
            ]

            if log_data.get("details") is None:
                log_data["details"] = {}

            for field in uuid_fields:
                val = log_data.get(field)
                if val:
                    try:
                        if not isinstance(val, uuid.UUID):
                            log_data[field] = uuid.UUID(str(val))
                    except (ValueError, TypeError):
                        log_data["details"][f"original_{field}"] = str(val)
                        log_data[field] = None

            new_log = SystemLog(**log_data)
            self.session.add(new_log)
            await self.session.commit()
            await self.session.refresh(new_log)
            return new_log
        except AppError:
            raise
        except Exception as e:
            logger.error("failed_to_create_log_entry: %s", e)
            raise AppError(
                message=f"Failed to create log entry: {e!s}",
                status_code=500,
                error_code="LOG_CREATION_FAILED",
            ) from e
