"""Pydantic schemas for system log entries."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.constants.enums import LogLevel


class LogCreate(BaseModel):
    """Schema for creating a new system log entry.

    UUID fields accept strings and attempt automatic conversion to UUID
    in the route handler; originals are preserved in details on failure.
    """

    level: LogLevel
    service: str | None = None
    component: str | None = None
    event_type: str | None = None
    session_id: str | None = None
    candidate_id: str | None = None
    assessment_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    message: str
    details: dict[str, object] | None = None
    error_stack: str | None = None
    duration_ms: int | None = None
    status: str | None = None


class LogResponse(LogCreate):
    """Schema for a system log entry response."""

    id: UUID
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
