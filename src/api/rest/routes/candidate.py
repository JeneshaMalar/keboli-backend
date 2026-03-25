"""Candidate management routes for CRUD and bulk upload operations."""

import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.core.services.candidate_service import CandidateService
from src.data.models.recruiter import Recruiter
from src.schemas.candidate_schema import CandidateCreate, CandidateResponse

router = APIRouter(prefix="/candidate", tags=["candidate"])


class MessageResponse(BaseModel):
    """Generic success message response."""

    message: str


class BulkUploadResponse(BaseModel):
    """Response model for the bulk upload endpoint."""

    created_count: int
    errors: list[str]


@router.post(
    "/",
    response_model=CandidateResponse,
    summary="Create a new candidate",
    description="Add a single candidate to the authenticated user's organization.",
)
async def create_candidate(
    payload: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> CandidateResponse:
    """Create a new candidate in the current organization.

    Args:
        payload: Candidate details (email, name, resume_url).
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        The newly created candidate.
    """
    service = CandidateService(db)
    return await service.create_candidate(org_id=current_user.org_id, data=payload)


@router.get(
    "/org-candidates",
    response_model=list[CandidateResponse],
    summary="List organization candidates",
    description="Retrieve all candidates belonging to the authenticated user's organization.",
)
async def get_org_candidates(
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> list[CandidateResponse]:
    """Retrieve all candidates for the current organization.

    Args:
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        List of candidates in the organization.
    """
    service = CandidateService(db)
    return await service.get_org_candidates(org_id=current_user.org_id)


@router.delete(
    "/{candidate_id}",
    response_model=MessageResponse,
    summary="Delete a candidate",
    description="Remove a candidate from the organization by their unique identifier.",
)
async def delete_candidate(
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> MessageResponse:
    """Delete a candidate from the organization.

    Args:
        candidate_id: UUID of the candidate to delete.
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        Success message confirming deletion.
    """
    service = CandidateService(db)
    result = await service.delete_candidate(
        org_id=current_user.org_id, candidate_id=candidate_id
    )
    return MessageResponse(message=result["message"])


@router.post(
    "/bulk-upload",
    response_model=BulkUploadResponse,
    summary="Bulk upload candidates via CSV",
    description="Upload a CSV file to create multiple candidates at once.",
)
async def bulk_upload_candidates(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> BulkUploadResponse:
    """Process a CSV file to create multiple candidates.

    Args:
        file: The uploaded CSV file containing 'email' and 'name' columns.
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        BulkUploadResponse with count of created records and any errors.
    """
    service = CandidateService(db)
    result = await service.bulk_upload_candidates(org_id=current_user.org_id, file=file)
    return BulkUploadResponse(
        created_count=result["created_count"], errors=result["errors"]
    )
