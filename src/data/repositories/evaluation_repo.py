"""Evaluation repository for encapsulating evaluation-related data queries."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.data.models.evaluation import Evaluation
from src.data.models.interview_session import InterviewSession
from src.data.models.invitation import Invitation
from src.data.models.candidate import Candidate


class EvaluationRepository:
    """Data-access layer for Evaluation entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(
        self, session_id: uuid.UUID, evaluation_data: dict[str, Any]
    ) -> Evaluation:
        """Upsert an evaluation record for a session."""
        query = select(Evaluation).where(Evaluation.session_id == session_id)
        result = await self.session.execute(query)
        evaluation = result.scalar_one_or_none()

        if evaluation:
            for key, value in evaluation_data.items():
                if hasattr(evaluation, key) and value is not None:
                    setattr(evaluation, key, value)
        else:
            evaluation_data["session_id"] = session_id
            evaluation = Evaluation(**evaluation_data)
            self.session.add(evaluation)

        await self.session.commit()
        await self.session.refresh(evaluation)
        return evaluation

    async def get_by_session(self, session_id: uuid.UUID) -> Evaluation | None:
        """Fetch an evaluation by session ID."""
        query = select(Evaluation).where(Evaluation.session_id == session_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_decision(
        self, session_id: uuid.UUID, update_data: dict[str, Any]
    ) -> Evaluation | None:
        """Apply updates to an existing evaluation."""
        evaluation = await self.get_by_session(session_id)
        if not evaluation:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(evaluation, key, value)

        await self.session.commit()
        await self.session.refresh(evaluation)
        return evaluation

    async def get_session_with_relations(
        self, session_id: uuid.UUID
    ) -> InterviewSession | None:
        """Fetch an interview session with evaluation, transcript, and candidate data."""
        session_query = (
            select(InterviewSession)
            .where(InterviewSession.id == session_id)
            .options(
                joinedload(InterviewSession.evaluation),
                joinedload(InterviewSession.transcript),
                joinedload(InterviewSession.invitation).joinedload(
                    Invitation.candidate
                ),
                joinedload(InterviewSession.invitation).joinedload(
                    Invitation.assessment
                ),
            )
        )
        result = await self.session.execute(session_query)
        return result.scalar_one_or_none()

    async def get_org_evaluations(self, org_id: uuid.UUID) -> list[InterviewSession]:
        """Retrieve all completed sessions with evaluations for an organization."""
        query = (
            select(InterviewSession)
            .join(Invitation, InterviewSession.invitation_id == Invitation.id)
            .join(Candidate, Invitation.candidate_id == Candidate.id)
            .where(Candidate.org_id == org_id)
            .options(
                joinedload(InterviewSession.evaluation),
                joinedload(InterviewSession.invitation).joinedload(
                    Invitation.candidate
                ),
                joinedload(InterviewSession.invitation).joinedload(
                    Invitation.assessment
                ),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())
