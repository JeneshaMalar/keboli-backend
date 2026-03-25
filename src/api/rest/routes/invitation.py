"""Invitation management routes for creating, listing, revoking, and validating invitations."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.core.services.invitation_service import InvitationService
from src.data.models.recruiter import Recruiter
from src.schemas.invitation_schema import InvitationCreate, InvitationResponse

router = APIRouter(prefix="/invitation", tags=["invitation"])


class InvitationCreateResponse(BaseModel):
    """Response returned when a new invitation is created."""

    invitation_id: str
    token: str
    expires_at: str
    candidate_email: str


class InvitationRevokeResponse(BaseModel):
    """Response returned when an invitation is revoked."""

    message: str
    invitation_id: str


@router.post(
    "/",
    response_model=InvitationCreateResponse,
    summary="Create a candidate invitation",
    description="Generate a secure invitation link and email it to the candidate.",
)
async def create_invitation(
    payload: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> InvitationCreateResponse:
    """Create and send a new invitation for a candidate.

    Args:
        payload: Invitation details (candidate_id, assessment_id, expiry).
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        InvitationCreateResponse with the token and expiration details.
    """
    service = InvitationService(db)
    result = await service.create_invitation(
        org_id=current_user.org_id,
        candidate_id=payload.candidate_id,
        assessment_id=payload.assessment_id,
        expires_in_hours=payload.expires_in_hours or 48,
    )
    return InvitationCreateResponse(
        invitation_id=str(result["invitation_id"]),
        token=result["token"],
        expires_at=str(result["expires_at"]),
        candidate_email=result["candidate_email"],
    )


@router.get(
    "/org-invitations",
    response_model=list[InvitationResponse],
    summary="List organization invitations",
    description="Retrieve all invitations for the authenticated user's organization.",
)
async def get_org_invitations(
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> list[InvitationResponse]:
    """Retrieve all invitations across the current organization.

    Args:
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        List of invitations for the organization.
    """
    service = InvitationService(db)
    return await service.get_org_invitations(org_id=current_user.org_id)


@router.patch(
    "/{invitation_id}/revoke",
    response_model=InvitationRevokeResponse,
    summary="Revoke an invitation",
    description="Manually expire an invitation to prevent further candidate access.",
)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> InvitationRevokeResponse:
    """Revoke an active invitation.

    Args:
        invitation_id: UUID of the invitation to revoke.
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        InvitationRevokeResponse confirming the revocation.
    """
    service = InvitationService(db)
    result = await service.revoke_invitation(
        org_id=current_user.org_id, invitation_id=invitation_id
    )
    return InvitationRevokeResponse(
        message=result["message"],
        invitation_id=str(result["invitation_id"]),
    )


@router.get(
    "/validate/{token}",
    response_model=InvitationResponse,
    summary="Validate an invitation token",
    description="Verify that an invitation token is valid, active, and not expired.",
)
async def validate_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> InvitationResponse:
    """Validate an invitation token for a candidate.

    Args:
        token: The secure URL-safe token to validate.
        db: Async database session.

    Returns:
        The validated invitation details.
    """
    service = InvitationService(db)
    return await service.validate_token(token)
