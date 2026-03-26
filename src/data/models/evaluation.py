"""SQLAlchemy model representing an AI-generated interview evaluation."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants.enums import HiringRecommendation
from src.data.models.base import Base


class Evaluation(Base):
    """AI-generated evaluation result for a completed interview session.

    Contains scoring across multiple dimensions, an AI summary,
    a hiring recommendation, and optional admin overrides.
    """

    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id"),
        unique=True,
        nullable=False,
    )
    technical_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    communication_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    confidence_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    cultural_alignment_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    total_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(
        MutableDict.as_mutable(JSONB), nullable=True
    )
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    hiring_recommendation: Mapped[HiringRecommendation | None] = mapped_column(
        PG_ENUM(
            HiringRecommendation,
            name="hiringrecommendation",
            create_type=False,
        ),
        nullable=True,
    )
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_recommendation: Mapped[HiringRecommendation | None] = mapped_column(
        PG_ENUM(
            HiringRecommendation,
            name="hiringrecommendation",
            create_type=False,
        ),
        nullable=True,
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_tie_winner: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false"
    )
    detailed_analysis: Mapped[dict[str, Any] | None] = mapped_column(
        MutableDict.as_mutable(JSONB), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session = relationship("InterviewSession", back_populates="evaluation")
