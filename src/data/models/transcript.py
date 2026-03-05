import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import DateTime, Integer, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableList
from src.data.models.base import Base

class Transcript(Base):
    __tablename__ = "interview_transcripts"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), primary_key=True)

    full_transcript: Mapped[List[Dict[str, Any]]] = mapped_column(
        MutableList.as_mutable(JSONB), nullable=False, default=list, server_default="[]"
    )

    transcript_gcs_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="transcript")