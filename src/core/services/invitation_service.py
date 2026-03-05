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

class InvitationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = InvitationRepository(session)
        self.candidate_repo = CandidateRepository(session)
        self.assessment_repo = AssessmentRepository(session)

    async def create_invitation(self, org_id: uuid.UUID, candidate_id: uuid.UUID, assessment_id: uuid.UUID, expires_in_hours: int = 48):
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
        
        return {
            "invitation_id": invitation.id,
            "token": token,
            "expires_at": expires_at,
            "candidate_email": candidate.email
        }

    async def get_org_invitations(self, org_id: uuid.UUID):
        return await self.repo.get_multi_by_org(org_id)

    async def revoke_invitation(self, org_id: uuid.UUID, invitation_id: uuid.UUID):
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
        invitation = await self.repo.get_by_token(token)
        if not invitation:
            try:
                inv_id = uuid.UUID(token)
                invitation = await self.repo.get_by_id(inv_id)
            except ValueError:
                pass
                
        if not invitation:
             raise HTTPException(status_code=404, detail="Invalid invitation token")
             
        if invitation.status == InvitationStatus.EXPIRED or invitation.expires_at < datetime.now(timezone.utc):
             raise HTTPException(status_code=403, detail="Invitation has expired")
             
        return invitation
