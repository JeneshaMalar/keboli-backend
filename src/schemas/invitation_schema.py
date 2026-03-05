import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from src.constants.enums import InvitationStatus
from src.schemas.candidate_schema import CandidateResponse

class InvitationCreate(BaseModel):
    candidate_id: uuid.UUID
    assessment_id: uuid.UUID
    expires_in_hours: Optional[int] = 48

class InvitationResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    assessment_id: uuid.UUID
    token: str
    expires_at: datetime
    status: InvitationStatus
    sent_at: datetime
    latest_session_id: Optional[uuid.UUID] = None
    latest_session_status: Optional[str] = None
    total_score: Optional[float] = None
    hiring_recommendation: Optional[str] = None
    
    candidate: Optional[CandidateResponse] = None

    model_config = ConfigDict(from_attributes=True)
