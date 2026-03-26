"""SQLAlchemy model representing an in-app notification for hiring managers."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.data.models.base import Base


class Notification(Base):
    """An in-app notification delivered to a hiring manager.

    Notifications are created when key events occur (e.g. interview
    completion) and link to the relevant page via target_path.
    """

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hiring_managers.id", ondelete="CASCADE"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    target_path: Mapped[str] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
