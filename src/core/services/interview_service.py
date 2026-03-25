import asyncio
import json
import logging
import uuid
from datetime import datetime
from uuid import UUID

import httpx
from fastapi import WebSocket
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload, selectinload

from src.config.settings import settings
from src.constants.enums import InterviewSessionStatus, InvitationStatus
from src.data.models.assessment import Assessment
from src.data.models.interview_session import InterviewSession
from src.data.models.invitation import Invitation

# from src.core.ai.llm.groq_client import GroqLLMClient
from src.data.repositories.interview_transcript_repo import (
    InterviewTranscriptRepository,
)
from src.handlers.audio.deepgram_stt import DeepgramSTT
from src.handlers.audio.deepgram_tts import deepgram_tts_bytes
from src.handlers.audio.ffmpeg_pipe import PCMTranscoder

logger = logging.getLogger(__name__)


class InterviewService:
    """This service manages the lifecycle of an interview session, including handling WebSocket communication,
    managing the interview state, and interacting with the database to store transcripts and session information.
    This is currently not used in this application,because webrtc is used for real-time communication instead of websockets.
    However, it can be adapted for use with websockets if needed in the future."""

    def __init__(
        self,
        db,
        session_id: UUID,
        assessment_id: str,
        invitation_id: UUID | None = None,
    ):
        self.db = db
        self.session_id = session_id
        self.assessment_id = assessment_id
        self.invitation_id = invitation_id
        self.agent_state = None
        self.agent_url = "http://interview_agent:8001/chat"

        self.transcript_repo = InterviewTranscriptRepository(db)

        self.transcoder = PCMTranscoder()
        self.transcoder.start()

        self.llm = None
        self.stt = DeepgramSTT(self.transcoder)

        self.is_completed = False
        self.heartbeat_task = None
        self.db_lock = asyncio.Lock()

    async def _get_agent_response(
        self, last_message: str | None = None
    ) -> tuple[str, bool]:
        """
        Communicate with the AI agent to get the next interview question or response.

        Args:
            last_message: The transcribed text from the candidate, if any.

        Returns:
            A tuple containing (response_text, is_session_completed_flag).
        """
        payload = {
            "session_id": str(self.session_id),
            "assessment_id": str(self.assessment_id),
            "last_message": last_message,
            "state": self.agent_state,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.agent_url, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                self.agent_state = data.get("state")
                return data.get("response", ""), data.get("is_completed", False)
        except Exception:
            if last_message:
                return f"I heard: {last_message}", False
            return (
                "Hello, I am having some trouble connecting to my brain. Let me try again later.",
                False,
            )

    async def _trigger_evaluation(self):
        """
        Notify the evaluation service to start analyzing the completed interview.

        Args:
            None

        Raises:
            httpx.HTTPStatusError: If the evaluation service returns a non-200 response.

        Returns:
            None
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.EVALUATION_SERVICE_URL}/api/v1/evaluate/{self.session_id}"
                response = await client.post(url, timeout=300.0)
                response.raise_for_status()
        except Exception as e:
            logger.error(
                f"Failed to trigger evaluation for session {self.session_id}: {e}"
            )

    async def complete_session(self, auto_evaluate: bool = True):
        """
        Finalize the interview session, update statuses, and stop background tasks.

        Args:
            auto_evaluate: Whether to automatically trigger the evaluation service.

        Returns:
            None
        """
        if self.is_completed:
            return

        self.is_completed = True

        async with self.db_lock:
            query = (
                update(InterviewSession)
                .where(InterviewSession.id == self.session_id)
                .values(
                    status=InterviewSessionStatus.COMPLETED,
                    completed_at=datetime.utcnow(),
                )
            )
            await self.db.execute(query)

            if self.invitation_id:
                inv_query = (
                    update(Invitation)
                    .where(Invitation.id == self.invitation_id)
                    .values(status=InvitationStatus.COMPLETED)
                )
                await self.db.execute(inv_query)

            await self.db.commit()

        if auto_evaluate:
            asyncio.create_task(self._trigger_evaluation())
        else:
            logger.info(
                f"Session {self.session_id} marked as completed without auto-evaluation."
            )

    async def _heartbeat_loop(self):
        """
        Background loop to update session 'last_heartbeat' and decrement remaining time.

        Args:
            None

        Returns:
            None
        """
        try:
            while not self.is_completed:
                await asyncio.sleep(5)
                async with self.db_lock:
                    query = (
                        update(InterviewSession)
                        .where(InterviewSession.id == self.session_id)
                        .values(
                            last_heartbeat=datetime.utcnow(),
                            remaining_seconds=InterviewSession.remaining_seconds - 5,
                        )
                    )
                    await self.db.execute(query)
                    await self.db.commit()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in heartbeat loop for session {self.session_id}: {e}")

    async def start(self, ws: WebSocket):
        """
        Start an interview session.

        Args:
            ws: WebSocket connection for real-time communication

        Raises:
            HTTPException: If session initialization fails

        Returns:
            None (streams responses via WebSocket)
        """
        async with self.db_lock:
            session = await self.db.scalar(
                select(InterviewSession).where(InterviewSession.id == self.session_id)
            )

            if not session:
                duration_mins = 60
                candidate_id = None

                if self.invitation_id:
                    invitation = await self.db.scalar(
                        select(Invitation)
                        .options(selectinload(Invitation.assessment))
                        .where(Invitation.id == self.invitation_id)
                    )

                    if invitation:
                        duration_mins = (
                            invitation.assessment.duration_minutes
                            if invitation.assessment
                            else 60
                        )
                        candidate_id = invitation.candidate_id

                        invitation.status = InvitationStatus.CLICKED
                    else:
                        logger.warning(
                            f"Invitation {self.invitation_id} not found for session {self.session_id}"
                        )

                elif self.assessment_id:
                    assessment = await self.db.get(
                        Assessment,
                        UUID(self.assessment_id)
                        if isinstance(self.assessment_id, str)
                        else self.assessment_id,
                    )
                    if assessment:
                        duration_mins = assessment.duration_minutes
                    else:
                        logger.warning(
                            f"Assessment {self.assessment_id} not found for session {self.session_id}"
                        )

                if not candidate_id:
                    candidate_id = uuid.uuid4()

                session = InterviewSession(
                    id=self.session_id,
                    invitation_id=self.invitation_id,
                    candidate_id=candidate_id,
                    status=InterviewSessionStatus.IN_PROGRESS,
                    remaining_seconds=duration_mins * 60,
                    started_at=datetime.utcnow(),
                )
                self.db.add(session)
            elif session:
                session.status = InterviewSessionStatus.IN_PROGRESS
                if not session.started_at:
                    session.started_at = datetime.utcnow()

                if session.remaining_seconds == 3600 or session.remaining_seconds <= 0:
                    asmt = None
                    if session.invitation_id:
                        inv = await self.db.scalar(
                            select(Invitation)
                            .options(joinedload(Invitation.assessment))
                            .where(Invitation.id == session.invitation_id)
                        )
                        asmt = inv.assessment if inv else None
                    elif self.assessment_id:
                        asmt = await self.db.get(
                            Assessment,
                            UUID(self.assessment_id)
                            if isinstance(self.assessment_id, str)
                            else self.assessment_id,
                        )

                    if asmt and session.remaining_seconds == 3600:
                        session.remaining_seconds = asmt.duration_minutes * 60

            await self.db.commit()

        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        greeting_text, is_end = await self._get_agent_response()

        async with self.db_lock:
            await self.transcript_repo.append_turn(
                self.session_id, "interviewer", greeting_text
            )

        await ws.send_text(json.dumps({"type": "tts_start", "text": greeting_text}))
        audio = await deepgram_tts_bytes(greeting_text)
        await ws.send_bytes(audio)
        await ws.send_text(json.dumps({"type": "tts_end"}))

        async def handle_final(full: str, confidence: float | None):
            if self.is_completed:
                return

            await ws.send_text(
                json.dumps({"type": "final", "text": full, "confidence": confidence})
            )

            async with self.db_lock:
                await self.transcript_repo.append_turn(
                    self.session_id, "candidate", full
                )

            llm_text, is_end = await self._get_agent_response(full)

            async with self.db_lock:
                await self.transcript_repo.append_turn(
                    self.session_id, "interviewer", llm_text
                )

            await ws.send_text(json.dumps({"type": "tts_start", "text": llm_text}))
            audio = await deepgram_tts_bytes(llm_text)
            await ws.send_bytes(audio)
            await ws.send_text(json.dumps({"type": "tts_end"}))

            if is_end:
                await ws.send_text(json.dumps({"type": "session_completed"}))
                await self.complete_session(auto_evaluate=True)

        await self.stt.connect(ws, handle_final)

    def write_audio(self, chunk: bytes):
        """
        Feed raw audio chunks from the client into the transcoder.

        Args:
            chunk: Binary audio data.
        """
        self.transcoder.write(chunk)

    async def on_disconnect(self):
        """
        Handle WebSocket disconnection by ensuring the session is finalized.
        """
        if not self.is_completed:
            await self.complete_session(auto_evaluate=True)

    def close(self):
        """
        Cleanup resources, cancel heartbeats, and close audio pipes.
        """
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        self.transcoder.close()
