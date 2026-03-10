import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import DateTime, Text, String, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PG_ENUM
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from src.data.models.base import Base
from src.constants.enums import LogLevel


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    level: Mapped[LogLevel] = mapped_column(
        PG_ENUM(
            LogLevel,
            name="loglevel",
            create_type=False
        ),
        nullable=False
    )

    service: Mapped[Optional[str]] = mapped_column(String(100))
    component: Mapped[Optional[str]] = mapped_column(String(100))
    event_type: Mapped[Optional[str]] = mapped_column(String(150))

    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    candidate_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    request_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    message: Mapped[str] = mapped_column(Text)

    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSONB),
        nullable=True
    )

    error_stack: Mapped[Optional[str]] = mapped_column(Text)

    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)

    status: Mapped[Optional[str]] = mapped_column(String(50))