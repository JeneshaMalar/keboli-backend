"""LiveKit service for managing WebRTC interview sessions and token generation."""

import logging
import uuid
from datetime import datetime
from typing import Any

from livekit.api import AccessToken, VideoGrants
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.config.settings import settings
from src.constants.enums import InterviewSessionStatus, InvitationStatus
from src.core.exceptions import AppError, NotFoundError, ValidationError
from src.data.models.assessment import Assessment
from src.data.models.candidate import Candidate
from src.data.models.interview_session import InterviewSession
from src.data.models.invitation import Invitation
from src.data.models.transcript import Transcript
from src.data.repositories.interview_transcript_repo import (
    InterviewTranscriptRepository,
)

logger = logging.getLogger(__name__)


class LiveKitService:
    """Service layer for managing LiveKit-based WebRTC interview sessions.

    Handles session initialization, token generation, heartbeat tracking,
    session completion, transcript retrieval, and session lifecycle management.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.transcript_repo = InterviewTranscriptRepository(session)

    async def get_or_create_session(
        self,
        session_id: uuid.UUID,
        invitation_id: uuid.UUID | None,
        assessment_id: uuid.UUID | None,
    ) -> dict[str, Any]:
        """Get an existing interview session or create a new one.

        Resolves the assessment duration from either the invitation or
        assessment directly. Generates a LiveKit room token.

        Args:
            session_id: UUID for the session (client-generated).
            invitation_id: Optional invitation UUID linking to candidate + assessment.
            assessment_id: Optional direct assessment UUID (fallback).

        Returns:
            A dictionary containing session metadata and the LiveKit token.

        Raises:
            ValidationError: If neither invitation_id nor assessment_id is provided.
        """
        existing = await self.session.get(InterviewSession, session_id)

        if existing:
            token = self._generate_token(str(session_id))
            return {
                "session_id": str(existing.id),
                "status": existing.status.value,
                "remaining_seconds": existing.remaining_seconds,
                "token": token,
                "livekit_url": settings.LIVEKIT_URL,
            }

        duration_minutes = 60
        candidate_id: uuid.UUID | None = None
        resolved_assessment_id: uuid.UUID | None = assessment_id

        if invitation_id:
            invitation = await self.session.get(Invitation, invitation_id)
            if invitation:
                if invitation.assessment:
                    duration_minutes = invitation.assessment.duration_minutes or 60
                    resolved_assessment_id = invitation.assessment_id
                candidate_id = invitation.candidate_id

                if invitation.status == InvitationStatus.SENT:
                    invitation.status = InvitationStatus.CLICKED
                    await self.session.flush()
        elif assessment_id:
            assessment = await self.session.get(Assessment, assessment_id)
            if assessment:
                duration_minutes = assessment.duration_minutes or 60

        if not candidate_id:
            candidate_id = uuid.uuid4()

        new_session = InterviewSession(
            id=session_id,
            invitation_id=invitation_id,
            candidate_id=candidate_id,
            status=InterviewSessionStatus.IN_PROGRESS,
            remaining_seconds=duration_minutes * 60,
            started_at=datetime.utcnow(),
        )
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)

        token = self._generate_token(str(session_id))
        return {
            "session_id": str(new_session.id),
            "status": new_session.status.value,
            "remaining_seconds": new_session.remaining_seconds,
            "token": token,
            "livekit_url": settings.LIVEKIT_URL,
        }

    def _generate_token(self, session_id: str) -> str:
        """Generate a LiveKit access token for the given session room.

        Args:
            session_id: The room name (session UUID string).

        Returns:
            A signed JWT token string for LiveKit authentication.
        """
        token = AccessToken(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
        token.with_identity(f"candidate-{session_id}")
        token.with_grants(
            VideoGrants(
                room_join=True,
                room=session_id,
            )
        )
        return token.to_jwt()

    async def update_heartbeat(
        self,
        session_id: uuid.UUID,
        remaining_seconds: int | None = None,
    ) -> dict[str, str]:
        """Update the heartbeat timestamp and optionally sync remaining time.

        Args:
            session_id: UUID of the interview session.
            remaining_seconds: Optional client-reported remaining seconds.

        Returns:
            A status confirmation dictionary.
        """
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
        return {"status": "ok"}

    async def complete_session(
        self,
        session_id: uuid.UUID,
    ) -> dict[str, str]:
        """Mark an interview session as completed.

        Args:
            session_id: UUID of the session to complete.

        Returns:
            A status confirmation with the session ID.

        Raises:
            NotFoundError: If the session does not exist.
        """
        interview_session = await self.session.get(InterviewSession, session_id)
        if not interview_session:
            raise NotFoundError(
                resource="InterviewSession", resource_id=str(session_id)
            )

        query = (
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(
                status=InterviewSessionStatus.COMPLETED,
                completed_at=datetime.utcnow(),
            )
        )
        await self.session.execute(query)

        if interview_session.invitation_id:
            inv_query = (
                update(Invitation)
                .where(Invitation.id == interview_session.invitation_id)
                .values(status=InvitationStatus.COMPLETED)
            )
            await self.session.execute(inv_query)

        await self.session.commit()
        return {"status": "completed", "session_id": str(session_id)}

    async def get_transcript(
        self,
        session_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Retrieve the full transcript for a session.

        Args:
            session_id: UUID of the interview session.

        Returns:
            A dictionary with the transcript data.
        """
        transcript = await self.transcript_repo.get_or_create(session_id)
        return {
            "session_id": str(session_id),
            "full_transcript": transcript.full_transcript if transcript else [],
            "turn_count": transcript.turn_count if transcript else 0,
        }

    async def update_session_field(
        self,
        session_id: uuid.UUID,
        **kwargs: Any,
    ) -> dict[str, str]:
        """Update arbitrary fields on an interview session.

        Args:
            session_id: UUID of the interview session.
            **kwargs: Column-value pairs to update.

        Returns:
            A status confirmation dictionary.
        """
        query = (
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(**kwargs)
        )
        await self.session.execute(query)
        await self.session.commit()
        return {"status": "updated"}
