import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class CandidateBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    resume_url: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class CandidateResponse(CandidateBase):
    id: uuid.UUID
    org_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
