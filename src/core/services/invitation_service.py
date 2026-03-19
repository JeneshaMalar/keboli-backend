import secrets
from datetime import datetime, timedelta, timezone
import uuid
from typing import List, Optional
from fastapi import HTTPException
from src.data.repositories.invitation_repo import InvitationRepository
from src.data.repositories.candidate_repo import CandidateRepository
from src.data.repositories.assessment_repo import AssessmentRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.constants.enums import InvitationStatus
from src.core.services.email_service import EmailService
from sqlalchemy import select, update
from src.data.models.invitation import Invitation
from src.data.models.candidate import Candidate
class InvitationService:
    """
    Service responsible for managing the candidate invitation lifecycle,
    including secure token generation, expiration tracking, and email dispatch.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = InvitationRepository(session)
        self.candidate_repo = CandidateRepository(session)
        self.assessment_repo = AssessmentRepository(session)

    async def create_invitation(self, org_id: uuid.UUID, candidate_id: uuid.UUID, assessment_id: uuid.UUID, expires_in_hours: int = 48):
        """
        Generate a secure invitation token and notify the candidate via email.

        Args:
            org_id: The organization ID owning the candidate and assessment
            candidate_id: UUID of the candidate to invite
            assessment_id: UUID of the assessment to assign
            expires_in_hours: Duration until the invitation token becomes invalid

        Raises:
            HTTPException: If the candidate or assessment is not found or belongs to another org

        Returns:
            A dictionary containing the invitation ID, secure token, and expiration timestamp
        """
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        if not candidate or candidate.org_id != org_id:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        assessment = await self.assessment_repo.get_by_id(assessment_id)
        if not assessment or assessment.org_id != org_id:
            raise HTTPException(status_code=404, detail="Assessment not found")
            
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        
        invitation_data = {
            "candidate_id": candidate_id,
            "assessment_id": assessment_id,
            "token": token,
            "expires_at": expires_at,
            "status": InvitationStatus.SENT
        }
        
        invitation = await self.repo.create(invitation_data)
        await self.session.commit()
        await self.session.refresh(invitation)

        email_service = EmailService()
        await email_service.send_invitation_email(
            candidate_email=candidate.email,
            candidate_name=candidate.name,
            assessment_title=assessment.title,
            token=token
            )

        
        return {
            "invitation_id": invitation.id,
            "token": token,
            "expires_at": expires_at,
            "candidate_email": candidate.email
        }

    async def get_org_invitations(self, org_id: uuid.UUID):
        """
        Retrieve all invitations for an organization, automatically marking expired ones.

        Args:
            org_id: Unique identifier of the organization

        Returns:
            A list of all invitations associated with the organization's candidates
        """
        candidates_query = select(Candidate.id).where(Candidate.org_id == org_id)
        update_query = (
            update(Invitation)
            .where(
                Invitation.candidate_id.in_(candidates_query),
                Invitation.expires_at < datetime.now(timezone.utc),
                Invitation.status.not_in([InvitationStatus.EXPIRED, InvitationStatus.COMPLETED])
            )
            .values(status=InvitationStatus.EXPIRED)
        )
        await self.session.execute(update_query)
        await self.session.commit()
        
        return await self.repo.get_multi_by_org(org_id)

    async def revoke_invitation(self, org_id: uuid.UUID, invitation_id: uuid.UUID):
        """
        Manually expire an invitation to prevent further access.

        Args:
            org_id: Organization ID for authorization check
            invitation_id: UUID of the invitation to revoke

        Raises:
            HTTPException: If invitation is not found or candidate belongs to another org

        Returns:
            A success message and the affected invitation ID
        """
        invitation = await self.repo.get_by_id(invitation_id)
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")
            
        candidate = await self.candidate_repo.get_by_id(invitation.candidate_id)
        if not candidate or candidate.org_id != org_id:
            raise HTTPException(status_code=403, detail="Forbidden")
            
        
        updated = await self.repo.update(invitation_id, status=InvitationStatus.EXPIRED)
        await self.session.commit()
        return {"message": "Invitation revoked", "invitation_id": invitation_id}

    async def validate_token(self, token: str):
        """
        Verify if a provided token is valid, active, and not yet expired.

        Args:
            token: The secure URL-safe token (or UUID string) to validate

        Raises:
            HTTPException (404): If the token does not exist
            HTTPException (403): If the invitation has expired

        Returns:
            The validated Invitation object
        """
        invitation = await self.repo.get_by_token(token)
        if not invitation:
            try:
                inv_id = uuid.UUID(token)
                invitation = await self.repo.get_by_id(inv_id)
            except ValueError:
                pass
                
        if not invitation:
             raise HTTPException(status_code=404, detail="Invalid invitation token")
             
        if invitation.status != InvitationStatus.EXPIRED and invitation.expires_at < datetime.now(timezone.utc):
             invitation.status = InvitationStatus.EXPIRED
             await self.session.commit()
             
        if invitation.status == InvitationStatus.EXPIRED:
             raise HTTPException(status_code=403, detail="Invitation has expired")
             
        return invitation
