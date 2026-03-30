"""System log service for persisting structured log entries."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AppError
from src.data.models.system_log import SystemLog
from src.constants.enums import LogLevel

logger = logging.getLogger(__name__)


from typing import Any
from src.data.repositories.log_repo import LogRepository

class LogService:
    """Service layer for persisting structured system log entries.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: Any) -> None:
        self.repo = LogRepository(session)

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

            level_input = log_data.get("level")
            if isinstance(level_input, str):
                try:
                    log_data["level"] = LogLevel(level_input.upper())
                except ValueError:
                    log_data["level"] = LogLevel.INFO
            elif level_input is None:
                log_data["level"] = LogLevel.INFO

            for field in uuid_fields:
                val = log_data.get(field)
                if val:
                    try:
                        if not isinstance(val, uuid.UUID):
                            log_data[field] = uuid.UUID(str(val))
                    except (ValueError, TypeError):
                        log_data["details"][f"original_{field}"] = str(val)
                        log_data[field] = None

            if log_data.get("status"):
                log_data["status"] = str(log_data["status"])[:50]

          
            valid_keys = {
                "id", "timestamp", "level", "service", "component", "event_type",
                "session_id", "candidate_id", "assessment_id", "user_id",
                "request_id", "ip_address", "user_agent", "message", "details",
                "error_stack", "duration_ms", "status"
            }
            sanitized_data = {
                k: v for k, v in log_data.items()
                if k in valid_keys and v is not None
            }

            new_log = await self.repo.create(sanitized_data)
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
