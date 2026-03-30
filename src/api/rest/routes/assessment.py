"""Assessment management routes for CRUD operations and skill graph updates."""

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db, CurrentRecruiter
from src.core.exceptions import NotFoundError
from src.core.services.assessment_service import AssessmentService
from src.schemas.assessment_schema import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentUpdate,
)

router = APIRouter(prefix="/assessment", tags=["assessment"])


class SkillGraphUpdate(BaseModel):
    """Schema for updating an assessment's AI-generated skill graph."""

    skill_graph: dict


@router.post(
    "/",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assessment",
    description="Create a new interview assessment with AI question generation configuration.",
)
async def create_new_assessment(
    payload: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentRecruiter = Depends(get_current_recruiter),
) -> AssessmentResponse:
    """Create a new assessment for the authenticated user's organization.

    Args:
        payload: Assessment creation data including title, JD, and scoring config.
        db: Async database session.
        current_user: The authenticated recruiter making the request.

    Returns:
        The newly created assessment.
    """
    service = AssessmentService(db)
    assessment = await service.create_assessment(
        current_user.org_id, payload.model_dump()
    )
    return AssessmentResponse.model_validate(assessment)


@router.get(
    "/org-assessments",
    response_model=list[AssessmentResponse],
    summary="List organization assessments",
    description="List all assessments belonging to the authenticated user's organization.",
)
async def get_org_assessments(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentRecruiter = Depends(get_current_recruiter),
) -> list[AssessmentResponse]:
    """List all assessments for the authenticated user's organization.

    Args:
        db: Async database session.
        current_user: The authenticated recruiter making the request.

    Returns:
        A list of all organization assessments.
    """
    service = AssessmentService(db)
    assessments = await service.get_org_assessments(current_user.org_id)
    return [AssessmentResponse.model_validate(a) for a in assessments]


@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Get assessment details",
    description="Retrieve a single assessment by its UUID.",
)
async def get_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """Retrieve a single assessment by its UUID.

    Args:
        assessment_id: UUID of the assessment to retrieve.
        db: Async database session.

    Returns:
        The requested assessment details.

    Raises:
        NotFoundError: If no assessment matches the given UUID.
    """
    service = AssessmentService(db)
    assessment = await service.get_assessment(assessment_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))
    return AssessmentResponse.model_validate(assessment)


@router.put(
    "/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Update an assessment",
    description="Update an existing assessment's configuration by UUID.",
)
async def update_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentRecruiter = Depends(get_current_recruiter),
) -> AssessmentResponse:
    """Update specific fields of an existing assessment.

    Args:
        assessment_id: UUID of the assessment to update.
        payload: Partial update containing only changed fields.
        db: Async database session.
        current_user: The authenticated recruiter making the request.

    Returns:
        The updated assessment.

    Raises:
        NotFoundError: If no assessment matches the given UUID.
    """
    service = AssessmentService(db)
    assessment = await service.get_assessment(assessment_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))

    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        updated = await service.update_assessment(assessment_id, update_data)
        return AssessmentResponse.model_validate(updated)
    return AssessmentResponse.model_validate(assessment)


@router.patch(
    "/{assessment_id}/toggle",
    response_model=AssessmentResponse,
    summary="Toggle assessment status",
    description="Activate or deactivate an assessment to control candidate access.",
)
async def toggle_assessment_status(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentRecruiter = Depends(get_current_recruiter),
) -> AssessmentResponse:
    """Toggle the active status of an assessment.

    Args:
        assessment_id: UUID of the assessment to toggle.
        db: Async database session.
        current_user: The authenticated recruiter making the request.

    Returns:
        The assessment with its updated active status.

    Raises:
        NotFoundError: If no assessment matches the given UUID.
    """
    service = AssessmentService(db)
    assessment = await service.get_assessment(assessment_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))

    updated = await service.toggle_status(assessment_id, not assessment.is_active)
    return AssessmentResponse.model_validate(updated)


@router.patch(
    "/{assessment_id}/skill-graph",
    response_model=AssessmentResponse,
    summary="Update skill graph",
    description="Replace the AI-generated skill graph on an assessment.",
)
async def update_skill_graph(
    assessment_id: uuid.UUID,
    payload: SkillGraphUpdate,
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """Update the skill graph for a specific assessment.

    This endpoint is typically called by the interview agent service
    after asynchronous skill graph generation.

    Args:
        assessment_id: UUID of the assessment to update.
        payload: The new skill graph data.
        db: Async database session.

    Returns:
        The assessment with its updated skill graph.

    Raises:
        NotFoundError: If no assessment matches the given UUID.
    """
    service = AssessmentService(db)
    assessment = await service.get_assessment(assessment_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))

    updated = await service.update_assessment(assessment_id, {"skill_graph": payload.skill_graph})
    return AssessmentResponse.model_validate(updated)
