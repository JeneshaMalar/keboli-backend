"""Pydantic schemas for evaluation reports and updates."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.constants.enums import HiringRecommendation


class EvaluationCreate(BaseModel):
    """Schema for creating or submitting an evaluation report."""

    technical_score: float
    communication_score: float
    confidence_score: float
    cultural_alignment_score: float
    total_score: float
    score_breakdown: dict[str, object]
    ai_summary: str
    ai_explanation: str | None = None
    hiring_recommendation: HiringRecommendation
    admin_recommendation: HiringRecommendation | None = None
    admin_notes: str | None = None
    is_tie_winner: bool = False
    detailed_analysis: dict[str, object] | None = None


class EvaluationResponse(EvaluationCreate):
    """Schema for an evaluation report response."""

    id: uuid.UUID
    session_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationUpdate(BaseModel):
    """Schema for updating an evaluation with admin overrides."""

    admin_recommendation: HiringRecommendation | None = None
    admin_notes: str | None = None
    is_tie_winner: bool | None = None


class EvaluationReportResponse(BaseModel):
    """Full evaluation report including candidate and transcript data."""

    evaluation: EvaluationResponse | None = None
    transcript: dict[str, object] | None = None
    candidate: dict[str, object] | None = None

    model_config = ConfigDict(from_attributes=True)
