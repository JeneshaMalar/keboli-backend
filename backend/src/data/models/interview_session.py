import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.models.base import Base
from src.constants.enums import InterviewSessionStatus


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invitation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("invitations.id"), nullable=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    status: Mapped[InterviewSessionStatus] = mapped_column(
        PG_ENUM(
            InterviewSessionStatus,
            name="interviewsessionstatus",
            create_type=False,
        ),
        nullable=False,
    )
    current_skill: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    difficulty_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    remaining_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    refresh_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    invitation = relationship("Invitation", back_populates="sessions")
    transcript = relationship("Transcript", uselist=False, back_populates="session")
    evaluation = relationship("Evaluation", uselist=False, back_populates="session")