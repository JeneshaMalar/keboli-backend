"""Pydantic schemas for candidate request/response serialization."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateBase(BaseModel):
    """Base schema containing shared candidate fields."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    resume_url: str | None = None


class CandidateCreate(CandidateBase):
    """Schema for creating a new candidate."""


class CandidateResponse(CandidateBase):
    """Schema for candidate API responses with server-generated fields."""

    id: uuid.UUID
    org_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
