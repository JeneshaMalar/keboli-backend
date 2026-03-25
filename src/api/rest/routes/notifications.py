"""Notification routes for managing in-app notifications."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.data.models.notification import Notification
from src.data.models.recruiter import Recruiter

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    """Response model for a single notification."""

    id: str
    message: str
    target_path: str | None
    is_read: bool
    created_at: datetime


class StatusResponse(BaseModel):
    """Generic status response."""

    status: str


@router.get(
    "/",
    response_model=list[NotificationOut],
    summary="List notifications",
    description="Retrieve the 20 most recent notifications for the authenticated user.",
)
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> list[NotificationOut]:
    """Retrieve the latest notifications for the current user.

    Args:
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        List of the 20 most recent notifications.
    """
    query = (
        select(Notification)
        .where(Notification.recruiter_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
    )
    result = await db.execute(query)
    notifications = result.scalars().all()

    return [
        NotificationOut(
            id=str(notif.id),
            message=notif.message,
            target_path=notif.target_path,
            is_read=notif.is_read,
            created_at=notif.created_at,
        )
        for notif in notifications
    ]


@router.patch(
    "/{notification_id}/read",
    response_model=StatusResponse,
    summary="Mark notification as read",
    description="Mark a specific notification as read for the authenticated user.",
)
async def mark_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> StatusResponse:
    """Mark a notification as read.

    Args:
        notification_id: UUID string of the notification.
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        StatusResponse confirming the operation.
    """
    await db.execute(
        update(Notification)
        .where(Notification.id == uuid.UUID(notification_id))
        .where(Notification.recruiter_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    return StatusResponse(status="success")
