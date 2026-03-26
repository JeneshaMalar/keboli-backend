"""Repository for interview transcript persistence operations."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from src.data.models.transcript import Transcript as InterviewTranscript

logger = logging.getLogger(__name__)


class InterviewTranscriptRepository:
    """Data-access layer for interview transcripts.

    Handles atomic get-or-create semantics and concurrent-safe
    transcript appending with row-level locking (SELECT … FOR UPDATE).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create(
        self, session_id: UUID, for_update: bool = False
    ) -> InterviewTranscript:
        """Retrieve an existing transcript or create a new empty one.

        Args:
            session_id: UUID of the interview session.
            for_update: If True, acquire a row-level lock for safe mutation.

        Returns:
            The existing or newly created InterviewTranscript.
        """
        stmt = select(InterviewTranscript).where(
            InterviewTranscript.session_id == session_id
        )
        if for_update:
            stmt = stmt.with_for_update()

        result = await self.db.execute(stmt)
        transcript = result.scalar_one_or_none()

        if not transcript:
            try:
                transcript = InterviewTranscript(
                    session_id=session_id, full_transcript=[], turn_count=0
                )
                self.db.add(transcript)
                await self.db.commit()
                await self.db.refresh(transcript)

                if for_update:
                    stmt = (
                        select(InterviewTranscript)
                        .where(InterviewTranscript.session_id == session_id)
                        .with_for_update()
                    )
                    result = await self.db.execute(stmt)
                    transcript = result.scalar_one_or_none()
            except Exception:
                await self.db.rollback()
                logger.warning(
                    "Concurrent transcript creation for session %s, retrying fetch",
                    session_id,
                )
                stmt = select(InterviewTranscript).where(
                    InterviewTranscript.session_id == session_id
                )
                if for_update:
                    stmt = stmt.with_for_update()
                result = await self.db.execute(stmt)
                transcript = result.scalar_one_or_none()

        return transcript

    async def append_turn(self, session_id: UUID, role: str, text: str) -> None:
        """Append a single conversation turn to the transcript.

        Args:
            session_id: UUID of the interview session.
            role: Speaker role ('interviewer' or 'candidate').
            text: The spoken text content.
        """
        try:
            transcript = await self.get_or_create(session_id, for_update=True)

            if transcript.full_transcript is None:
                transcript.full_transcript = []

            transcript.full_transcript.append({"role": role, "text": text})
            flag_modified(transcript, "full_transcript")

            transcript.turn_count += 1

            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e
