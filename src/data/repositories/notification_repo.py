"""Repository for notification persistence operations."""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.notification import Notification


class NotificationRepository:
    """Data-access layer for Notification entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_notifications(
        self, recruiter_id: uuid.UUID, limit: int = 20
    ) -> list[Notification]:
        """Fetch the most recent notifications for a user."""
        query = (
            select(Notification)
            .where(Notification.recruiter_id == recruiter_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_as_read(
        self, notification_id: uuid.UUID, recruiter_id: uuid.UUID
    ) -> None:
        """Mark a notification as read and commit."""
        await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.recruiter_id == recruiter_id)
            .values(is_read=True)
        )
        await self.session.commit()
