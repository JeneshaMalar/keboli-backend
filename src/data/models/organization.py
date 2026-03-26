"""SQLAlchemy model representing an organization (workspace)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.data.models.recruiter import Recruiter

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.models.base import Base


class Organization(Base):
    """A tenant workspace that owns recruiters, candidates, and assessments.

    Each organization is an isolated workspace with its own pool of
    hiring managers, candidates, assessments, and invitation data.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    recruiters: Mapped[list["Recruiter"]] = relationship(
        "Recruiter", back_populates="organization"
    )
