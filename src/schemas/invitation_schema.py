"""Pydantic schemas for invitation request/response serialization."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.constants.enums import InvitationStatus
from src.schemas.candidate_schema import CandidateResponse
from src.schemas.assessment_schema import AssessmentResponse


class InvitationCreate(BaseModel):
    """Schema for creating a new candidate invitation."""

    candidate_id: uuid.UUID
    assessment_id: uuid.UUID
    expires_in_hours: int | None = 48


class InvitationResponse(BaseModel):
    """Schema for invitation API responses with computed session data."""

    id: uuid.UUID
    candidate_id: uuid.UUID
    assessment_id: uuid.UUID
    token: str
    expires_at: datetime
    status: InvitationStatus
    sent_at: datetime
    latest_session_id: uuid.UUID | None = None
    latest_session_status: str | None = None
    total_score: float | None = None
    hiring_recommendation: str | None = None

    candidate: CandidateResponse | None = None
    assessment: AssessmentResponse | None = None

    model_config = ConfigDict(from_attributes=True)
