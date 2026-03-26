"""SQLAlchemy model representing an interview transcript."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.data.models.interview_session import InterviewSession

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.models.base import Base


class Transcript(Base):
    """Full interview transcript for a session, stored as structured JSON.

    Each entry in full_transcript contains a role (interviewer/candidate)
    and the corresponding text, preserving the conversation order.
    """

    __tablename__ = "interview_transcripts"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), primary_key=True
    )

    full_transcript: Mapped[list[dict[str, Any]]] = mapped_column(
        MutableList.as_mutable(JSONB), nullable=False, default=list, server_default="[]"
    )

    transcript_gcs_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    turn_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="transcript"
    )
