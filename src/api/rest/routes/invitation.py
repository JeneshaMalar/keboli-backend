from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from src.api.rest.dependencies import get_current_recruiter, get_db
from src.data.models.recruiter import Recruiter
from src.schemas.invitation_schema import InvitationCreate, InvitationResponse
from src.core.services.invitation_service import InvitationService
from typing import List

router = APIRouter(prefix="/invitation", tags=["invitation"])

@router.post("/")
async def create_invitation(
    payload: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    service = InvitationService(db)
    return await service.create_invitation(
        org_id=current_user.org_id,
        candidate_id=payload.candidate_id,
        assessment_id=payload.assessment_id,
        expires_in_hours=payload.expires_in_hours
    )

@router.get("/org-invitations", response_model=List[InvitationResponse])
async def get_org_invitations(
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    service = InvitationService(db)
    return await service.get_org_invitations(org_id=current_user.org_id)

@router.patch("/{invitation_id}/revoke")
async def revoke_invitation(
    invitation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    service = InvitationService(db)
    return await service.revoke_invitation(org_id=current_user.org_id, invitation_id=invitation_id)

@router.get("/validate/{token}")
async def validate_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    
    service = InvitationService(db)
    return await service.validate_token(token)
