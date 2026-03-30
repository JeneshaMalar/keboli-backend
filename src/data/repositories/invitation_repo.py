"""Repository for invitation persistence operations."""

import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.data.models.candidate import Candidate
from src.data.models.invitation import Invitation
from src.data.models.interview_session import InterviewSession
from src.constants.enums import InvitationStatus
from datetime import datetime, timezone


class InvitationRepository:
    """Data-access layer for Invitation entities.

    Provides CRUD helpers with eager-loading strategies for related
    candidate, assessment, and session data.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, invitation_data: dict[str, object]) -> Invitation:
        """Insert a new invitation record.

        Args:
            invitation_data: Column values for the new invitation.

        Returns:
            The created Invitation instance (flushed, not committed).
        """
        instance = Invitation(**invitation_data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, invitation_id: uuid.UUID) -> Invitation | None:
        """Fetch a single invitation by primary key with related data.

        Args:
            invitation_id: UUID of the invitation.

        Returns:
            The Invitation with candidate and assessment loaded, or None.
        """

        query = (
            select(Invitation)
            .where(Invitation.id == invitation_id)
            .options(
                joinedload(Invitation.candidate),
                joinedload(Invitation.assessment),
                selectinload(Invitation.sessions).selectinload(
                    InterviewSession.evaluation
                ),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> Invitation | None:
        """Look up an invitation by its secure URL-safe token.

        Args:
            token: The invitation token string.

        Returns:
            The Invitation with candidate and assessment loaded, or None.
        """

        query = (
            select(Invitation)
            .where(Invitation.token == token)
            .options(
                joinedload(Invitation.candidate),
                joinedload(Invitation.assessment),
                selectinload(Invitation.sessions).selectinload(
                    InterviewSession.evaluation
                ),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_by_org(self, org_id: uuid.UUID) -> list[Invitation]:
        """Retrieve all invitations for an organization with related data.

        Args:
            org_id: UUID of the organization.

        Returns:
            List of invitations with candidate, session, and evaluation data loaded.
        """

        query = (
            select(Invitation)
            .join(Candidate)
            .where(Candidate.org_id == org_id)
            .options(
                joinedload(Invitation.candidate),
                joinedload(Invitation.assessment),
                selectinload(Invitation.sessions).selectinload(
                    InterviewSession.evaluation
                ),
            )
            .order_by(Invitation.sent_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, invitation_id: uuid.UUID, **kwargs: object) -> Invitation:
        """Update an invitation's fields by primary key.

        Args:
            invitation_id: UUID of the invitation to update.
            **kwargs: Column-value pairs to set.

        Returns:
            The updated Invitation instance.
        """
        query = (
            update(Invitation)
            .where(Invitation.id == invitation_id)
            .values(**kwargs)
            .returning(Invitation)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one()

    async def delete(self, invitation_id: uuid.UUID) -> None:
        """Delete an invitation by primary key.

        Args:
            invitation_id: UUID of the invitation to remove.
        """
        query = delete(Invitation).where(Invitation.id == invitation_id)
        await self.session.execute(query)
        await self.session.commit()

    async def mark_expired_for_org(self, org_id: uuid.UUID) -> None:
        """Mark eligible invitations as expired for a specific organization."""
        candidates_query = select(Candidate.id).where(Candidate.org_id == org_id)
        update_query = (
            update(Invitation)
            .where(
                Invitation.candidate_id.in_(candidates_query),
                Invitation.expires_at < datetime.now(timezone.utc),
                Invitation.status.not_in(
                    [InvitationStatus.EXPIRED, InvitationStatus.COMPLETED]
                ),
            )
            .values(status=InvitationStatus.EXPIRED)
        )
        await self.session.execute(update_query)
        await self.session.commit()
