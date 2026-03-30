"""Repository for system log persistence operations."""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.data.models.system_log import SystemLog


class LogRepository:
    """Data-access layer for SystemLog entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, log_data: dict[str, Any]) -> SystemLog:
        """Insert a new system log record.

        Args:
            log_data: Column values for the new system log.

        Returns:
            The created SystemLog instance.
        """
        instance = SystemLog(**log_data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
