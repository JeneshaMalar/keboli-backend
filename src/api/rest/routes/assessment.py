"""Assessment management routes for CRUD operations and skill graph updates."""

import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.services.assessment_service import AssessmentService
from src.core.utils.file_processing import extract_text_from_file
from src.data.models.assessment import Assessment
from src.data.models.recruiter import Recruiter
from src.schemas.assessment_schema import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentUpdate,
)

router = APIRouter(prefix="/assessment", tags=["assessment"])


class SkillGraphUpdate(BaseModel):
    """Request body for updating an assessment's skill graph."""

    skill_graph: dict[str, object]


class MessageResponse(BaseModel):
    """Generic success message response."""

    message: str


@router.post(
    "/",
    response_model=AssessmentResponse,
    summary="Create a new assessment",
    description="Create a new assessment from a JSON payload for the authenticated user's organization.",
)
async def create_new_assessment(
    payload: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> Assessment:
    """Create a new assessment with the provided details.

    Args:
        payload: Assessment creation data (title, JD, duration, etc.).
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        The newly created assessment.
    """
    service = AssessmentService(db)
    return await service.create_assessment(
        org_id=current_user.org_id, data=payload.model_dump()
    )


@router.post(
    "/create-with-file",
    response_model=AssessmentResponse,
    summary="Create assessment from uploaded JD file",
    description="Create a new assessment by extracting the job description from a PDF/DOCX file or raw text.",
)
async def create_assessment_with_file(
    title: str = Form(...),
    duration_minutes: int = Form(30),
    passing_score: int = Form(60),
    difficulty_level: str = Form("medium"),
    max_attempts: int = Form(1),
    is_active: bool = Form(True),
    file: UploadFile | None = File(None),
    raw_text: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> Assessment:
    """Create an assessment by extracting JD text from an uploaded file.

    Args:
        title: Assessment title.
        duration_minutes: Time limit in minutes.
        passing_score: Minimum passing score (0-100).
        difficulty_level: One of easy, medium, hard.
        max_attempts: Maximum number of attempts allowed.
        is_active: Whether the assessment is active.
        file: Optional uploaded PDF/DOCX file.
        raw_text: Optional raw text of the job description.
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        The newly created assessment.

    Raises:
        ValidationError: If no job description is provided.
    """
    if file is not None:
        content = await file.read()
        job_description = await extract_text_from_file(
            content, file.filename or "unknown.txt"
        )
    else:
        job_description = raw_text

    if not job_description:
        raise ValidationError(
            message="job_description is required", field="job_description"
        )

    payload = {
        "title": title,
        "job_description": job_description,
        "duration_minutes": duration_minutes,
        "passing_score": passing_score,
        "difficulty_level": difficulty_level,
        "max_attempts": max_attempts,
        "is_active": is_active,
    }

    service = AssessmentService(db)
    return await service.create_assessment(org_id=current_user.org_id, data=payload)


@router.get(
    "/org-assessments",
    response_model=list[AssessmentResponse],
    summary="List organization assessments",
    description="Retrieve all assessments belonging to the authenticated user's organization.",
)
async def get_org_assessments(
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> list[Assessment]:
    """Retrieve all assessments for the current user's organization.

    Args:
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        List of assessments belonging to the organization.
    """
    query = select(Assessment).where(Assessment.org_id == current_user.org_id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Get assessment by ID",
    description="Retrieve a single assessment by its unique identifier.",
)
async def get_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
) -> Assessment:
    """Retrieve a single assessment by its UUID.

    Args:
        assessment_id: String UUID of the assessment.
        db: Async database session.

    Returns:
        The requested assessment.

    Raises:
        NotFoundError: If the assessment does not exist.
    """
    try:
        valid_id = uuid.UUID(assessment_id)
    except ValueError as e:
        raise NotFoundError(resource="Assessment", resource_id=assessment_id) from e

    service = AssessmentService(db)
    assessment = await service.repo.get_by_id(valid_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=assessment_id)
    return assessment


@router.patch(
    "/{assessment_id}/skills",
    response_model=AssessmentResponse,
    summary="Update assessment skill graph",
    description="Replace the skill graph for the specified assessment.",
)
async def update_assessment_skills(
    assessment_id: str,
    payload: SkillGraphUpdate,
    db: AsyncSession = Depends(get_db),
) -> Assessment:
    """Update the skill graph of an assessment.

    Args:
        assessment_id: String UUID of the assessment.
        payload: New skill graph data.
        db: Async database session.

    Returns:
        The updated assessment.

    Raises:
        NotFoundError: If the assessment does not exist.
    """
    try:
        valid_id = uuid.UUID(assessment_id)
    except ValueError as e:
        raise NotFoundError(resource="Assessment", resource_id=assessment_id) from e

    service = AssessmentService(db)
    result = await service.repo.update(valid_id, skill_graph=payload.skill_graph)
    await service.session.commit()
    return result


@router.patch(
    "/{assessment_id}/toggle",
    response_model=AssessmentResponse,
    summary="Toggle assessment active status",
    description="Activate or deactivate an assessment.",
)
async def toggle_assessment(
    assessment_id: uuid.UUID,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
) -> Assessment:
    """Toggle the active/inactive status of an assessment.

    Args:
        assessment_id: UUID of the assessment.
        is_active: Whether the assessment should be active.
        db: Async database session.

    Returns:
        The updated assessment.
    """
    service = AssessmentService(db)
    return await service.toggle_status(assessment_id, is_active)


@router.put(
    "/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Update assessment details",
    description="Update one or more fields of an existing assessment.",
)
async def update_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> Assessment:
    """Update fields of an existing assessment.

    Args:
        assessment_id: UUID of the assessment.
        payload: Fields to update (only provided fields are changed).
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        The updated assessment.

    Raises:
        NotFoundError: If the assessment is not found or doesn't belong to the org.
    """
    service = AssessmentService(db)
    assessment = await service.repo.get_by_id(assessment_id)

    if not assessment or assessment.org_id != current_user.org_id:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))

    update_data = dict(payload.model_dump(exclude_unset=True).items())
    updated = await service.repo.update(assessment_id, **update_data)
    await db.commit()
    await db.refresh(updated)
    return updated


@router.delete(
    "/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Soft-delete an assessment",
    description="Deactivate an assessment (soft delete) by setting is_active to false.",
)
async def delete_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> Assessment:
    """Soft-delete an assessment by marking it inactive.

    Args:
        assessment_id: UUID of the assessment.
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        The deactivated assessment.

    Raises:
        NotFoundError: If the assessment is not found or doesn't belong to the org.
    """
    service = AssessmentService(db)
    assessment = await service.repo.get_by_id(assessment_id)

    if not assessment or assessment.org_id != current_user.org_id:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))

    updated = await service.repo.update(assessment_id, is_active=False)
    await db.commit()
    await db.refresh(updated)
    return updated
