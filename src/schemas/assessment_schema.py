import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from src.constants.enums import DifficultyLevel
class AssessmentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, examples=["Senior Python Developer Test"])
    job_description: str = Field(..., min_length=1, description="The JD used by AI to generate questions")
    duration_minutes: int = Field(30, gt=0, le=300)
    passing_score: int = Field(60, ge=0, le=100)
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    max_attempts: int = Field(1, ge=1, le=5)
    is_active: bool = True
    skill_graph: Optional[dict] = None


class AssessmentCreate(AssessmentBase):
    pass


class AssessmentUpdate(BaseModel):
    title: Optional[str] = None
    job_description: Optional[str] = None
    duration_minutes: Optional[int] = None
    passing_score: Optional[int] = None
    difficulty_level: Optional[DifficultyLevel] = None
    max_attempts: Optional[int] = None
    is_active: Optional[bool] = None

class AssessmentResponse(AssessmentBase):
    id: uuid.UUID
    org_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)