from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Any
import uuid

from src.api.rest.dependencies import get_db, get_current_recruiter
from src.data.models.notification import Notification
from src.data.models.recruiter import Recruiter

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/")
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    query = (
        select(Notification)
        .where(Notification.recruiter_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
    )
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [
        {
            "id": str(notif.id),
            "message": notif.message,
            "target_path": notif.target_path,
            "is_read": notif.is_read,
            "created_at": notif.created_at
        }
        for notif in notifications
    ]

@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    await db.execute(
        update(Notification)
        .where(Notification.id == uuid.UUID(notification_id))
        .where(Notification.recruiter_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "success"}
