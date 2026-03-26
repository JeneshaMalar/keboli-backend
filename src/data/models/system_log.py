"""SQLAlchemy model representing a structured system log entry."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from src.constants.enums import LogLevel
from src.data.models.base import Base


class SystemLog(Base):
    """A structured log entry persisted to the database for observability.

    Captures request metadata, timing, error stacks, and contextual
    IDs (session, candidate, assessment) for end-to-end tracing.
    """

    __tablename__ = "system_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    level: Mapped[LogLevel] = mapped_column(
        PG_ENUM(LogLevel, name="loglevel", create_type=True, metadata=Base.metadata),
        nullable=False,
    )

    service: Mapped[str | None] = mapped_column(String(100))
    component: Mapped[str | None] = mapped_column(String(100))
    event_type: Mapped[str | None] = mapped_column(String(150))

    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(Text)

    message: Mapped[str] = mapped_column(Text)

    details: Mapped[dict[str, Any] | None] = mapped_column(
        MutableDict.as_mutable(JSONB), nullable=True
    )

    error_stack: Mapped[str | None] = mapped_column(Text)

    duration_ms: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str | None] = mapped_column(String(50))
