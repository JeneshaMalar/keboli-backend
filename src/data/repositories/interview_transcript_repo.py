from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm.attributes import flag_modified
from src.data.models.transcript import Transcript as InterviewTranscript

class InterviewTranscriptRepository:
    def __init__(self, db: AsyncSession): 
        self.db = db

    async def get_or_create(self, session_id: UUID, for_update: bool = False) -> InterviewTranscript:
        stmt = select(InterviewTranscript).where(InterviewTranscript.session_id == session_id)
        if for_update:
            stmt = stmt.with_for_update()
            
        result = await self.db.execute(stmt)
        transcript = result.scalar_one_or_none()

        if not transcript:
            try:
                transcript = InterviewTranscript(session_id=session_id, full_transcript=[], turn_count=0)
                self.db.add(transcript)
                await self.db.commit()
                await self.db.refresh(transcript)
                
                # If we need it for update, fetch it again with lock after creation
                if for_update:
                    stmt = select(InterviewTranscript).where(InterviewTranscript.session_id == session_id).with_for_update()
                    result = await self.db.execute(stmt)
                    transcript = result.scalar_one_or_none()
            except Exception:
                # If another process created it simultaneously, just fetch it
                await self.db.rollback()
                stmt = select(InterviewTranscript).where(InterviewTranscript.session_id == session_id)
                if for_update:
                    stmt = stmt.with_for_update()
                result = await self.db.execute(stmt)
                transcript = result.scalar_one_or_none()

        return transcript

    async def append_turn(self, session_id: UUID, role: str, text: str):
        try:
            transcript = await self.get_or_create(session_id, for_update=True)
            
            if transcript.full_transcript is None:
                transcript.full_transcript = []
                
            transcript.full_transcript.append({"role": role, "text": text})
            flag_modified(transcript, "full_transcript")

            transcript.turn_count += 1
            
            await self.db.commit()
            print(f"Successfully saved {role} turn.")
        except Exception as e:
            await self.db.rollback()
            print(f"Database error in append_turn: {e}")
            raise e