"""Candidate management routes for CRUD operations and bulk CSV upload."""

import uuid

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db, CurrentRecruiter
from src.core.services.candidate_service import CandidateService
from src.schemas.candidate_schema import CandidateResponse

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.post(
    "/",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a candidate",
    description="Register a new candidate within the authenticated user's organization.",
)
async def create_candidate(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentRecruiter = Depends(get_current_recruiter),
) -> CandidateResponse:
    """Create a new candidate in the current user's organization.

    Args:
        payload: Candidate creation data (email, name, optional resume_url).
        db: Async database session.
        current_user: The authenticated recruiter.

    Returns:
        The newly created candidate.
    """
    from src.schemas.candidate_schema import CandidateCreate

    data = CandidateCreate(**payload)
    service = CandidateService(db)
    candidate = await service.create_candidate(current_user.org_id, data)
    return CandidateResponse.model_validate(candidate)


@router.get(
    "/org-candidates",
    response_model=list[CandidateResponse],
    summary="List organization candidates",
    description="Retrieve all candidates belonging to the authenticated user's organization.",
)
async def get_candidates(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentRecruiter = Depends(get_current_recruiter),
) -> list[CandidateResponse]:
    """List all candidates for the current user's organization.

    Args:
        db: Async database session.
        current_user: The authenticated recruiter.

    Returns:
        A list of candidates in the organization.
    """
    service = CandidateService(db)
    candidates = await service.get_org_candidates(current_user.org_id)
    return [CandidateResponse.model_validate(c) for c in candidates]


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a candidate",
    description="Remove a candidate and all associated records from the organization.",
)
async def delete_candidate(
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentRecruiter = Depends(get_current_recruiter),
) -> dict[str, str]:
    """Delete a candidate by UUID.

    Args:
        candidate_id: UUID of the candidate to remove.
        db: Async database session.
        current_user: The authenticated recruiter.

    Returns:
        A success message dictionary.

    Raises:
        NotFoundError: If the candidate is not found or belongs to another org.
    """
    service = CandidateService(db)
    return await service.delete_candidate(current_user.org_id, candidate_id)


@router.post(
    "/bulk-upload",
    status_code=status.HTTP_200_OK,
    summary="Bulk upload candidates via CSV",
    description="Upload a CSV file to create multiple candidates at once.",
)
async def bulk_upload(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentRecruiter = Depends(get_current_recruiter),
) -> dict:
    """Process a CSV upload to create multiple candidates.

    The CSV file must contain 'email' and 'name' (or 'full name') columns.

    Args:
        file: The uploaded CSV file.
        db: Async database session.
        current_user: The authenticated recruiter.

    Returns:
        A dictionary with the count of created records and any row-level errors.
    """
    file_content = await file.read()
    try:
        service = CandidateService(db)
        return await service.bulk_upload_candidates(
            current_user.org_id, file_content, file.filename or ""
        )
    finally:
        await file.close()
