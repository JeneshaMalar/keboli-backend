from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from src.api.rest.dependencies import get_current_recruiter, get_db
from src.data.models.recruiter import Recruiter
from src.schemas.candidate_schema import CandidateCreate, CandidateResponse
from src.core.services.candidate_service import CandidateService

router = APIRouter(prefix="/candidate", tags=["candidate"])

@router.post("/", response_model=CandidateResponse)
async def create_candidate(
    payload: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    service = CandidateService(db)
    return await service.create_candidate(org_id=current_user.org_id, data=payload)

@router.get("/org-candidates", response_model=list[CandidateResponse])
async def get_org_candidates(
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    service = CandidateService(db)
    return await service.get_org_candidates(org_id=current_user.org_id)

@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    service = CandidateService(db)
    return await service.delete_candidate(org_id=current_user.org_id, candidate_id=candidate_id)

@router.post("/bulk-upload")
async def bulk_upload_candidates(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    service = CandidateService(db)
    return await service.bulk_upload_candidates(org_id=current_user.org_id, file=file)
