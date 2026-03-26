"""SQLAlchemy model representing a candidate interview invitation."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants.enums import InvitationStatus
from src.data.models.base import Base


class Invitation(Base):
    """An invitation linking a candidate to an assessment via a secure token.

    Tracks the invitation lifecycle from SENT through CLICKED to
    COMPLETED or EXPIRED, and provides computed properties for the
    latest session status and evaluation scores.
    """

    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[InvitationStatus] = mapped_column(
        PG_ENUM(InvitationStatus, name="invitationstatus", create_type=False),
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    candidate = relationship("Candidate", back_populates="invitations")
    assessment = relationship("Assessment")
    sessions = relationship("InterviewSession", back_populates="invitation")

    @property
    def latest_session_id(self) -> uuid.UUID | None:
        """Return the ID of the most recently created session, if any."""
        if not self.sessions:
            return None
        sorted_sessions = sorted(
            self.sessions, key=lambda s: s.created_at, reverse=True
        )
        return sorted_sessions[0].id

    @property
    def total_score(self) -> float | None:
        """Return the total evaluation score from the latest session, if available."""
        if not self.sessions:
            return None
        sorted_sessions = sorted(
            self.sessions, key=lambda s: s.created_at, reverse=True
        )
        latest = sorted_sessions[0]
        return (
            float(latest.evaluation.total_score)
            if latest.evaluation and latest.evaluation.total_score is not None
            else None
        )

    @property
    def hiring_recommendation(self) -> str | None:
        """Return the AI hiring recommendation from the latest session, if available."""
        if not self.sessions:
            return None
        sorted_sessions = sorted(
            self.sessions, key=lambda s: s.created_at, reverse=True
        )
        latest = sorted_sessions[0]
        return (
            latest.evaluation.hiring_recommendation.value
            if latest.evaluation and latest.evaluation.hiring_recommendation
            else None
        )

    @property
    def latest_session_status(self) -> str | None:
        """Return the status string of the most recently created session."""
        if not self.sessions:
            return None
        sorted_sessions = sorted(
            self.sessions, key=lambda s: s.created_at, reverse=True
        )
        return sorted_sessions[0].status.value if sorted_sessions[0].status else None
