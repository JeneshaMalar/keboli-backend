import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.models.base import Base
from src.constants.enums import InvitationStatus


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[InvitationStatus] = mapped_column(
        PG_ENUM(InvitationStatus, name="invitationstatus", create_type=False),
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="invitations")
    assessment = relationship("Assessment")
    sessions = relationship("InterviewSession", back_populates="invitation")

    @property
    def latest_session_id(self) -> Optional[uuid.UUID]:
        if not self.sessions:
            return None
        # Sort by creation time descending and get the first one
        sorted_sessions = sorted(self.sessions, key=lambda s: s.created_at, reverse=True)
        return sorted_sessions[0].id

    @property
    def total_score(self) -> Optional[float]:
        if not self.sessions:
            return None
        sorted_sessions = sorted(self.sessions, key=lambda s: s.created_at, reverse=True)
        latest = sorted_sessions[0]
        return float(latest.evaluation.total_score) if latest.evaluation and latest.evaluation.total_score is not None else None

    @property
    def hiring_recommendation(self) -> Optional[str]:
        if not self.sessions:
            return None
        sorted_sessions = sorted(self.sessions, key=lambda s: s.created_at, reverse=True)
        latest = sorted_sessions[0]
        return latest.evaluation.hiring_recommendation.value if latest.evaluation and latest.evaluation.hiring_recommendation else None

    @property
    def latest_session_status(self) -> Optional[str]:
        if not self.sessions:
            return None
        sorted_sessions = sorted(self.sessions, key=lambda s: s.created_at, reverse=True)
        return sorted_sessions[0].status.value if sorted_sessions[0].status else None