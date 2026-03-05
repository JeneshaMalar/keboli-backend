import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import DateTime, Float, Text, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PG_ENUM
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.models.base import Base
from src.constants.enums import HiringRecommendation


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), unique=True, nullable=False)
    technical_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    communication_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    cultural_alignment_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    total_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    score_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(MutableDict.as_mutable(JSONB), nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hiring_recommendation: Mapped[Optional[HiringRecommendation]] = mapped_column(
        PG_ENUM(
            HiringRecommendation,
            name="hiringrecommendation",
            create_type=False,
        ),
        nullable=True,
    )
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admin_recommendation: Mapped[Optional[HiringRecommendation]] = mapped_column(
        PG_ENUM(
            HiringRecommendation,
            name="hiringrecommendation",
            create_type=False,
        ),
        nullable=True,
    )
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_tie_winner: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    detailed_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(MutableDict.as_mutable(JSONB), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="evaluation")