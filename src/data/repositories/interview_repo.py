"""Repository for interview session persistence operations.

Provides data-access encapsulation for active interview sessions,
heartbeats, completion state, and evaluation polling.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.constants.enums import InterviewSessionStatus
from src.data.models.assessment import Assessment
from src.data.models.interview_session import InterviewSession
from src.data.models.invitation import Invitation


class InterviewRepository:
    """Data-access layer for InterviewSession entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, session_id: uuid.UUID) -> InterviewSession | None:
        """Fetch a single interview session by primary key."""
        return await self.session.get(InterviewSession, session_id)

    async def get_invitation(self, invitation_id: uuid.UUID) -> Invitation | None:
        """Fetch an invitation to resolve assessment duration."""
        return await self.session.get(Invitation, invitation_id)

    async def get_assessment(self, assessment_id: uuid.UUID) -> Assessment | None:
        """Fetch an assessment to resolve duration fallback."""
        return await self.session.get(Assessment, assessment_id)

    async def create(self, session_data: dict[str, Any]) -> InterviewSession:
        """Insert a new interview session."""
        instance = InterviewSession(**session_data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, session_id: uuid.UUID, **kwargs: Any) -> InterviewSession | None:
        """Update fields on an interview session."""
        query = (
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(**kwargs)
            .returning(InterviewSession)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def get_session_with_relations(
        self, session_id: uuid.UUID
    ) -> InterviewSession | None:
        """Fetch session with assessment and candidate relations."""
        query = (
            select(InterviewSession)
            .where(InterviewSession.id == session_id)
            .options(
                joinedload(InterviewSession.invitation).joinedload(
                    Invitation.assessment
                ),
                joinedload(InterviewSession.invitation).joinedload(
                    Invitation.candidate
                ),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_heartbeat(
        self, session_id: uuid.UUID, remaining_seconds: int | None = None
    ) -> None:
        """Update the heartbeat timestamp and optional remaining time."""
        values: dict[str, Any] = {"last_heartbeat": datetime.utcnow()}
        if remaining_seconds is not None:
            values["remaining_seconds"] = remaining_seconds

        query = (
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(**values)
        )
        await self.session.execute(query)
        await self.session.commit()
