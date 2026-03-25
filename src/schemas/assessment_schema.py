import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.constants.enums import DifficultyLevel


class AssessmentBase(BaseModel):
    title: str = Field(
        ..., min_length=3, max_length=255, examples=["Senior Python Developer Test"]
    )
    job_description: str = Field(
        ..., min_length=1, description="The JD used by AI to generate questions"
    )
    duration_minutes: int = Field(30, gt=0, le=300)
    passing_score: int = Field(60, ge=0, le=100)
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    max_attempts: int = Field(1, ge=1, le=5)
    is_active: bool = True
    skill_graph: dict | None = None


class AssessmentCreate(AssessmentBase):
    pass


class AssessmentUpdate(BaseModel):
    title: str | None = None
    job_description: str | None = None
    duration_minutes: int | None = None
    passing_score: int | None = None
    difficulty_level: DifficultyLevel | None = None
    max_attempts: int | None = None
    is_active: bool | None = None


class AssessmentResponse(AssessmentBase):
    id: uuid.UUID
    org_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
