import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    resume_url: str | None = None


class CandidateCreate(CandidateBase):
    pass


class CandidateResponse(CandidateBase):
    id: uuid.UUID
    org_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
