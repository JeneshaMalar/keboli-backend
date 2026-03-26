"""Notification routes for managing in-app notifications."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.core.services.notification_service import NotificationService
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
    service = NotificationService(db)
    results = await service.get_user_notifications(current_user.id)
    return [NotificationOut(**r) for r in results]


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
    service = NotificationService(db)
    result = await service.mark_as_read(uuid.UUID(notification_id), current_user.id)
    return StatusResponse(**result)
