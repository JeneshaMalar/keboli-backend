"""Health check service for monitoring database availability."""

from sqlalchemy import text
from typing import Any


class HealthService:
    """Service layer for health checks."""

    def __init__(self, session: Any) -> None:
        self.session = session

    async def check_db_connection(self) -> bool:
        """Execute a lightweight SQL query to verify database connectivity."""
        try:
            await self.session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
