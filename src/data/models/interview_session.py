import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants.enums import InterviewSessionStatus
from src.data.models.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invitation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invitations.id"), nullable=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    status: Mapped[InterviewSessionStatus] = mapped_column(
        PG_ENUM(
            InterviewSessionStatus,
            name="interviewsessionstatus",
            create_type=False,
        ),
        nullable=False,
    )
    current_skill: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remaining_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    refresh_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    egress_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    invitation = relationship("Invitation", back_populates="sessions")
    transcript = relationship("Transcript", uselist=False, back_populates="session")
    evaluation = relationship("Evaluation", uselist=False, back_populates="session")
