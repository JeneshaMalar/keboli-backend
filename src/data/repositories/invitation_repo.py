"""Repository for invitation persistence operations."""

import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.data.models.candidate import Candidate
from src.data.models.invitation import Invitation


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
        await self.session.flush()
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
                joinedload(Invitation.candidate), joinedload(Invitation.assessment)
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
                joinedload(Invitation.candidate), joinedload(Invitation.assessment)
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
        from src.data.models.interview_session import InterviewSession

        query = (
            select(Invitation)
            .join(Candidate)
            .where(Candidate.org_id == org_id)
            .options(
                joinedload(Invitation.candidate),
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
        return result.scalar_one()

    async def delete(self, invitation_id: uuid.UUID) -> None:
        """Delete an invitation by primary key.

        Args:
            invitation_id: UUID of the invitation to remove.
        """
        query = delete(Invitation).where(Invitation.id == invitation_id)
        await self.session.execute(query)
