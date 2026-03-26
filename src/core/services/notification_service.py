"""Notification service for managing in-app notification operations."""

import logging
import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.notification import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Service layer for managing in-app notifications.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_notifications(
        self, recruiter_id: uuid.UUID, limit: int = 20
    ) -> list[dict[str, object]]:
        """Retrieve the most recent notifications for a recruiter.

        Args:
            recruiter_id: UUID of the authenticated recruiter.
            limit: Maximum number of notifications to return.

        Returns:
            List of notification dictionaries.
        """
        query = (
            select(Notification)
            .where(Notification.recruiter_id == recruiter_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        notifications = result.scalars().all()

        return [
            {
                "id": str(notif.id),
                "message": notif.message,
                "target_path": notif.target_path,
                "is_read": notif.is_read,
                "created_at": notif.created_at,
            }
            for notif in notifications
        ]

    async def mark_as_read(
        self, notification_id: uuid.UUID, recruiter_id: uuid.UUID
    ) -> dict[str, str]:
        """Mark a specific notification as read for the authenticated user.

        Args:
            notification_id: UUID of the notification.
            recruiter_id: UUID of the authenticated recruiter (authorization check).

        Returns:
            A status confirmation dictionary.
        """
        await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.recruiter_id == recruiter_id)
            .values(is_read=True)
        )
        await self.session.commit()
        return {"status": "success"}
