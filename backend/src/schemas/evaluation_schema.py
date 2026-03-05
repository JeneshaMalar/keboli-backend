import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from src.constants.enums import HiringRecommendation

class EvaluationCreate(BaseModel):
    technical_score: float
    communication_score: float
    confidence_score: float
    cultural_alignment_score: float
    total_score: float
    score_breakdown: Dict[str, Any]
    ai_summary: str
    ai_explanation: Optional[str] = None
    hiring_recommendation: HiringRecommendation
    admin_recommendation: Optional[HiringRecommendation] = None
    admin_notes: Optional[str] = None
    is_tie_winner: bool = False
    detailed_analysis: Optional[Dict[str, Any]] = None

class EvaluationResponse(EvaluationCreate):
    id: uuid.UUID
    session_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class EvaluationUpdate(BaseModel):
    admin_recommendation: Optional[HiringRecommendation] = None
    admin_notes: Optional[str] = None
    is_tie_winner: Optional[bool] = None

class EvaluationReportResponse(BaseModel):
    evaluation: Optional[EvaluationResponse] = None
    transcript: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
