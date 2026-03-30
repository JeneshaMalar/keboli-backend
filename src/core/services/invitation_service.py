"""Invitation service for managing the candidate invitation lifecycle."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, update
from typing import Any

from src.constants.enums import InvitationStatus
from src.core.exceptions import ForbiddenError, NotFoundError
from src.core.services.email_service import EmailService
from src.data.models.candidate import Candidate
from src.data.models.invitation import Invitation
from src.data.repositories.assessment_repo import AssessmentRepository
from src.data.repositories.candidate_repo import CandidateRepository
from src.data.repositories.invitation_repo import InvitationRepository


class InvitationService:
    """Service responsible for managing the candidate invitation lifecycle,
    including secure token generation, expiration tracking, and email dispatch.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: Any) -> None:
        self.repo = InvitationRepository(session)
        self.candidate_repo = CandidateRepository(session)
        self.assessment_repo = AssessmentRepository(session)

    async def create_invitation(
        self,
        org_id: uuid.UUID,
        candidate_id: uuid.UUID,
        assessment_id: uuid.UUID,
        expires_in_hours: int = 48,
    ) -> dict[str, Any]:
        """Generate a secure invitation token and notify the candidate via email.

        Args:
            org_id: The organization ID owning the candidate and assessment.
            candidate_id: UUID of the candidate to invite.
            assessment_id: UUID of the assessment to assign.
            expires_in_hours: Duration until the invitation token becomes invalid.

        Returns:
            A dictionary containing the invitation ID, secure token, expiration,
            and candidate email.

        Raises:
            NotFoundError: If the candidate or assessment is not found or belongs to another org.
        """
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        if not candidate or candidate.org_id != org_id:
            raise NotFoundError(resource="Candidate", resource_id=str(candidate_id))

        assessment = await self.assessment_repo.get_by_id(assessment_id)
        if not assessment or assessment.org_id != org_id:
            raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        invitation_data = {
            "candidate_id": candidate_id,
            "assessment_id": assessment_id,
            "token": token,
            "expires_at": expires_at,
            "status": InvitationStatus.SENT,
        }

        invitation = await self.repo.create(invitation_data)

        email_service = EmailService()
        await email_service.send_invitation_email(
            candidate_email=candidate.email,
            candidate_name=candidate.name,
            assessment_title=assessment.title,
            token=token,
        )

        return {
            "invitation_id": invitation.id,
            "token": token,
            "expires_at": expires_at,
            "candidate_email": candidate.email,
        }

    async def get_org_invitations(self, org_id: uuid.UUID) -> list[Invitation]:
        """Retrieve all invitations for an organization, automatically marking expired ones.

        Args:
            org_id: Unique identifier of the organization.

        Returns:
            A list of all invitations associated with the organization's candidates.
        """
        await self.repo.mark_expired_for_org(org_id)
        return await self.repo.get_multi_by_org(org_id)

    async def revoke_invitation(
        self, org_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> dict[str, Any]:
        """Manually expire an invitation to prevent further access.

        Args:
            org_id: Organization ID for authorization check.
            invitation_id: UUID of the invitation to revoke.

        Returns:
            A success message and the affected invitation ID.

        Raises:
            NotFoundError: If the invitation is not found.
            ForbiddenError: If the candidate belongs to another organization.
        """
        invitation = await self.repo.get_by_id(invitation_id)
        if not invitation:
            raise NotFoundError(resource="Invitation", resource_id=str(invitation_id))

        candidate = await self.candidate_repo.get_by_id(invitation.candidate_id)
        if not candidate or candidate.org_id != org_id:
            raise ForbiddenError(message="Forbidden")

        await self.repo.update(invitation_id, status=InvitationStatus.EXPIRED)
        return {"message": "Invitation revoked", "invitation_id": invitation_id}

    async def validate_token(self, token: str) -> Invitation:
        """Verify if a provided token is valid, active, and not yet expired.

        Args:
            token: The secure URL-safe token (or UUID string) to validate.

        Returns:
            The validated Invitation object.

        Raises:
            NotFoundError: If the token does not exist.
            ForbiddenError: If the invitation has expired.
        """
        invitation = await self.repo.get_by_token(token)
        if not invitation:
            try:
                inv_id = uuid.UUID(token)
                invitation = await self.repo.get_by_id(inv_id)
            except ValueError:
                pass

        if not invitation:
            raise NotFoundError(resource="Invitation", resource_id=token)

        if (
            invitation.status != InvitationStatus.EXPIRED
            and invitation.expires_at < datetime.now(timezone.utc)
        ):
            invitation = await self.repo.update(invitation.id, status=InvitationStatus.EXPIRED)

        if invitation.status == InvitationStatus.EXPIRED:
            raise ForbiddenError(message="Invitation has expired")

        return invitation
