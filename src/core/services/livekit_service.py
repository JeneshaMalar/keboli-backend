"""LiveKit service for managing WebRTC interview sessions and token generation."""

import logging
import uuid
from datetime import datetime
from typing import Any

from livekit.api import AccessToken, VideoGrants
from typing import Any

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
from src.data.repositories.interview_repo import InterviewRepository
from src.data.repositories.invitation_repo import InvitationRepository
from src.core.services.evaluation_service import EvaluationService


logger = logging.getLogger(__name__)


class LiveKitService:
    """Service layer for managing LiveKit-based WebRTC interview sessions.

    Handles session initialization, token generation, heartbeat tracking,
    session completion, transcript retrieval, and session lifecycle management.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: Any) -> None:
        self.session = session
        self.repo = InterviewRepository(session)
        self.invitation_repo = InvitationRepository(session)
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
        existing = await self.repo.get_by_id(session_id)

        if existing:
            ass_id = "unknown"
            if existing.invitation_id:
                inv = await self.repo.get_invitation(existing.invitation_id)
                if inv and inv.assessment_id:
                    ass_id = str(inv.assessment_id)
            room_name = f"interview_{session_id}_{ass_id}"
            token = self._generate_token(str(session_id), room_name)
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
            invitation = await self.repo.get_invitation(invitation_id)
            if invitation:
                if invitation.assessment:
                    duration_minutes = invitation.assessment.duration_minutes or 60
                    resolved_assessment_id = invitation.assessment_id
                candidate_id = invitation.candidate_id

                if invitation.status == InvitationStatus.SENT:
                    await self.invitation_repo.update(invitation.id, status=InvitationStatus.CLICKED)
        elif assessment_id:
            assessment = await self.repo.get_assessment(assessment_id)
            if assessment:
                duration_minutes = assessment.duration_minutes or 60

        if not candidate_id:
            candidate_id = uuid.uuid4()

        new_session = await self.repo.create(
            {
                "id": session_id,
                "invitation_id": invitation_id,
                "candidate_id": candidate_id,
                "status": InterviewSessionStatus.IN_PROGRESS,
                "remaining_seconds": duration_minutes * 60,
                "started_at": datetime.utcnow(),
            }
        )

        room_name = f"interview_{session_id}_{resolved_assessment_id}"
        token = self._generate_token(str(session_id), room_name)
        return {
            "session_id": str(new_session.id),
            "status": new_session.status.value,
            "remaining_seconds": new_session.remaining_seconds,
            "token": token,
            "livekit_url": settings.LIVEKIT_URL,
        }

    def _generate_token(self, session_id: str, room_name: str) -> str:
        """Generate a LiveKit access token for the given session room.

        Args:
            session_id: The session UUID string.
            room_name: The correctly formatted room name to join.

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
                room=room_name,
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
        await self.repo.update_heartbeat(session_id, remaining_seconds)
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
        interview_session = await self.repo.get_by_id(session_id)
        if not interview_session:
            raise NotFoundError(
                resource="InterviewSession", resource_id=str(session_id)
            )

        await self.repo.update(
            session_id,
            status=InterviewSessionStatus.COMPLETED,
            completed_at=datetime.utcnow(),
        )

        if interview_session.invitation_id:
            await self.invitation_repo.update(
                interview_session.invitation_id, status=InvitationStatus.COMPLETED
            )
        
        try:
            eval_service = EvaluationService(self.session)
            await eval_service.trigger_evaluation(session_id)
            logger.info("Evaluation triggered successfully for session %s", session_id)
        except Exception as e:
            logger.error("Failed to trigger evaluation for session %s: %s", session_id, e)

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

    async def append_transcript(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
    ) -> dict[str, Any]:
        """Append a new turn to the interview transcript.

        Args:
            session_id: UUID of the interview session.
            role: Speaker role ('interviewer' or 'candidate').
            content: The text spoken in this turn.

        Returns:
            A status confirmation with the new turn count.
        """
        await self.transcript_repo.append_turn(
            session_id=session_id, role=role, text=content
        )
        return {"status": "appended", "session_id": str(session_id)}

    async def get_session_field(
        self,
        session_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Retrieve full session and assessment details for evaluation.

        Args:
            session_id: UUID of the interview session.

        Returns:
            A dictionary containing session, candidate, and assessment data.

        Raises:
            NotFoundError: If the session is not found.
        """
        session = await self.repo.get_session_with_relations(session_id)

        if not session:
            raise NotFoundError(resource="InterviewSession", resource_id=str(session_id))

        assessment_data = {}
        if session.invitation and session.invitation.assessment:
            asmt = session.invitation.assessment
            assessment_data = {
                "id": str(asmt.id),
                "title": asmt.title,
                "job_description": asmt.job_description,
                "skill_graph": asmt.skill_graph,
                "passing_score": asmt.passing_score,
            }

        return {
            "session_id": str(session.id),
            "status": session.status.value,
            "candidate_id": str(session.candidate_id),
            "assessment_details": assessment_data,
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
        await self.repo.update(session_id, **kwargs)
        return {"status": "updated"}
