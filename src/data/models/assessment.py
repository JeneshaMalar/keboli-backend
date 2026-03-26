"""SQLAlchemy model representing an interview assessment configuration."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants.enums import DifficultyLevel
from src.data.models.base import Base


class Assessment(Base):
    """An interview assessment owned by an organization.

    Stores the job description, scoring criteria, duration, and an
    optional AI-generated skill graph used to guide AI interviewers.
    """

    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)

    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    passing_score: Mapped[int] = mapped_column(Integer, default=60)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        PG_ENUM(DifficultyLevel, name="difficultylevel", create_type=False),
        nullable=False,
        server_default=DifficultyLevel.MEDIUM.value,
    )
    skill_graph: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization = relationship("Organization")
