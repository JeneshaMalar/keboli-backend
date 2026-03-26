"""Repository for candidate persistence operations."""

import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.candidate import Candidate
from src.data.models.evaluation import Evaluation
from src.data.models.interview_session import InterviewSession
from src.data.models.invitation import Invitation
from src.data.models.transcript import Transcript


class CandidateRepository:
    """Data-access layer for Candidate entities.

    Provides CRUD helpers including cascade-safe deletion of related
    sessions, evaluations, transcripts, and invitations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, candidate_data: dict[str, object]) -> Candidate:
        """Insert a new candidate record.

        Args:
            candidate_data: Column values for the new candidate.

        Returns:
            The created Candidate instance (flushed, not committed).
        """
        instance = Candidate(**candidate_data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def create_bulk(self, candidates_data: list[dict[str, object]]) -> list[Candidate]:
        """Insert multiple candidate records at once.

        Args:
            candidates_data: List of column-value dicts for each candidate.

        Returns:
            List of created Candidate instances.
        """
        instances = [Candidate(**data) for data in candidates_data]
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    async def get_by_id(self, candidate_id: uuid.UUID) -> Candidate | None:
        """Fetch a single candidate by primary key.

        Args:
            candidate_id: UUID of the candidate.

        Returns:
            The Candidate if found, otherwise None.
        """
        return await self.session.get(Candidate, candidate_id)

    async def get_by_email_and_org(
        self, email: str, org_id: uuid.UUID
    ) -> Candidate | None:
        """Look up a candidate by email within a specific organization.

        Args:
            email: Candidate email address.
            org_id: UUID of the organization.

        Returns:
            The Candidate if found, otherwise None.
        """
        query = select(Candidate).where(
            Candidate.email == email, Candidate.org_id == org_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_by_org(self, org_id: uuid.UUID) -> list[Candidate]:
        """Retrieve all candidates for an organization, newest first.

        Args:
            org_id: UUID of the organization.

        Returns:
            List of candidates ordered by creation date descending.
        """
        query = (
            select(Candidate)
            .where(Candidate.org_id == org_id)
            .order_by(Candidate.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, candidate_id: uuid.UUID, **kwargs: object) -> Candidate:
        """Update a candidate's fields by primary key.

        Args:
            candidate_id: UUID of the candidate to update.
            **kwargs: Column-value pairs to set.

        Returns:
            The updated Candidate instance.
        """
        query = (
            update(Candidate)
            .where(Candidate.id == candidate_id)
            .values(**kwargs)
            .returning(Candidate)
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def delete(self, candidate_id: uuid.UUID) -> None:
        """Delete a candidate and all related records (cascade-safe).

        Removes evaluations, transcripts, interview sessions, and
        invitations before deleting the candidate itself.

        Args:
            candidate_id: UUID of the candidate to remove.
        """
        sessions_query = select(InterviewSession.id).where(
            InterviewSession.candidate_id == candidate_id
        )
        sessions_result = await self.session.execute(sessions_query)
        session_ids = [row[0] for row in sessions_result.fetchall()]

        if session_ids:
            await self.session.execute(
                delete(Evaluation).where(Evaluation.session_id.in_(session_ids))
            )
            await self.session.execute(
                delete(Transcript).where(Transcript.session_id.in_(session_ids))
            )

        await self.session.execute(
            delete(InterviewSession).where(
                InterviewSession.candidate_id == candidate_id
            )
        )
        await self.session.execute(
            delete(Invitation).where(Invitation.candidate_id == candidate_id)
        )
        await self.session.execute(
            delete(Candidate).where(Candidate.id == candidate_id)
        )
