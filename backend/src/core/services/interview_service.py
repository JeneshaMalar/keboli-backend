import json
import asyncio
import httpx
from typing import Optional
from fastapi import WebSocket
import uuid
from uuid import UUID
from datetime import datetime
from src.data.models.assessment import Assessment

from src.handlers.audio.ffmpeg_pipe import PCMTranscoder
from src.handlers.audio.deepgram_tts import deepgram_tts_bytes
from src.handlers.audio.deepgram_stt import DeepgramSTT
from src.core.ai.llm.groq_client import GroqLLMClient 
from src.data.repositories.interview_transcript_repo import InterviewTranscriptRepository
from src.data.models.interview_session import InterviewSession
from src.data.models.invitation import Invitation
from sqlalchemy import select
from src.constants.enums import InterviewSessionStatus
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from src.constants.enums import InvitationStatus
from sqlalchemy.orm import joinedload
class InterviewService:

    def __init__(self, db, session_id: UUID, assessment_id: str, invitation_id: Optional[UUID] = None):
        self.db = db
        self.session_id = session_id
        self.assessment_id = assessment_id
        self.invitation_id = invitation_id
        self.agent_state = None
        self.agent_url = "http://localhost:8001/chat"
        
        self.transcript_repo = InterviewTranscriptRepository(db)

        self.transcoder = PCMTranscoder()
        self.transcoder.start()

        self.llm = GroqLLMClient()
        self.stt = DeepgramSTT(self.transcoder)
        
        self.is_completed = False
        self.heartbeat_task = None
        self.db_lock = asyncio.Lock()

    async def _get_agent_response(self, last_message: Optional[str] = None) -> tuple[str, bool]:
        payload = {
            "session_id": str(self.session_id),
            "assessment_id": str(self.assessment_id),
            "last_message": last_message,
            "state": self.agent_state
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.agent_url, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                self.agent_state = data.get("state")
                return data.get("response", ""), data.get("is_completed", False)
        except Exception as e:
            print(f"Agent error: {e}")
            if last_message:
                try:
                    return await self.llm.generate(last_message), False
                except:
                    return f"I heard: {last_message}", False
            return "Hello, I am having some trouble connecting to my brain. Let me try again later.", False

    async def _trigger_evaluation(self):
        try:
            async with httpx.AsyncClient() as client:
                url = f"http://localhost:8002/api/v1/evaluate/{self.session_id}"
                print(f"Triggering evaluation at {url}...")
                response = await client.post(url, timeout=300.0)
                response.raise_for_status()
                print("Evaluation agent triggered successfully")
        except Exception as e:
            print(f"Failed to trigger evaluation agent: {e}")

    async def complete_session(self, auto_evaluate: bool = True):
        if self.is_completed:
            return
        
        self.is_completed = True
        

        async with self.db_lock:
            query = (
                update(InterviewSession)
                .where(InterviewSession.id == self.session_id)
                .values(status=InterviewSessionStatus.COMPLETED, completed_at=datetime.utcnow())
            )
            await self.db.execute(query)
            await self.db.commit()
        
        if auto_evaluate:
            asyncio.create_task(self._trigger_evaluation())
        else:
            print(f"[DEBUG] Session {self.session_id} ended partialy/disconnected. Admin needs to click generate report.")

    async def _heartbeat_loop(self):
        
        
        print(f"[DEBUG] Starting heartbeat loop for session {self.session_id}")
        try:
            while not self.is_completed:
                await asyncio.sleep(5)
                async with self.db_lock:
                    query = (
                        update(InterviewSession)
                        .where(InterviewSession.id == self.session_id)
                        .values(
                            last_heartbeat=datetime.utcnow(),
                            remaining_seconds=InterviewSession.remaining_seconds - 5
                        )
                    )
                    await self.db.execute(query)
                    await self.db.commit()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[ERROR] Heartbeat error: {e}")

    async def start(self, ws: WebSocket):
        

        print(f"[DEBUG] InterviewService.start for session {self.session_id}")

        async with self.db_lock:
            session = await self.db.scalar(select(InterviewSession).where(InterviewSession.id == self.session_id))
            
            if not session:
                print(f"[DEBUG] Session {self.session_id} not found. Creating session...")
                
                duration_mins = 60
                candidate_id = None
                
                if self.invitation_id:
                    
                    invitation = await self.db.scalar(
                        select(Invitation)
                        .options(selectinload(Invitation.assessment))
                        .where(Invitation.id == self.invitation_id)
                    )
                    
                    if invitation:
                        duration_mins = invitation.assessment.duration_minutes if invitation.assessment else 60
                        candidate_id = invitation.candidate_id
                        
                        invitation.status = InvitationStatus.CLICKED
                    else:
                        print(f"[DEBUG] Error: Invitation {self.invitation_id} not found.")
                
                elif self.assessment_id:
                    assessment = await self.db.get(Assessment, UUID(self.assessment_id) if isinstance(self.assessment_id, str) else self.assessment_id)
                    if assessment:
                        duration_mins = assessment.duration_minutes
                    else:
                        print(f"[DEBUG] Error: Assessment {self.assessment_id} not found.")
                
                if not candidate_id:
                    candidate_id = uuid.uuid4() 

                session = InterviewSession(
                    id=self.session_id,
                    invitation_id=self.invitation_id,
                    candidate_id=candidate_id,
                    status=InterviewSessionStatus.IN_PROGRESS,
                    remaining_seconds=duration_mins * 60,
                    started_at=datetime.utcnow()
                )
                self.db.add(session)
                print(f"[DEBUG] Created new interview session with {duration_mins} mins duration: {self.session_id}")
            elif session:
                print(f"[DEBUG] Session {self.session_id} exists. Updating status to IN_PROGRESS.")
                session.status = InterviewSessionStatus.IN_PROGRESS
                if not session.started_at:
                    session.started_at = datetime.utcnow()
                
            
                if session.remaining_seconds == 3600 or session.remaining_seconds <= 0:
                     
                     
                     asmt = None
                     if session.invitation_id:
                         inv = await self.db.scalar(select(Invitation).options(joinedload(Invitation.assessment)).where(Invitation.id == session.invitation_id))
                         asmt = inv.assessment if inv else None
                     elif self.assessment_id:
                         asmt = await self.db.get(Assessment, UUID(self.assessment_id) if isinstance(self.assessment_id, str) else self.assessment_id)
                     
                     if asmt:
                         if session.remaining_seconds == 3600:
                            session.remaining_seconds = asmt.duration_minutes * 60
                            print(f"[DEBUG] Corrected remaining_seconds to {session.remaining_seconds} for session {self.session_id}")
            
            print("[DEBUG] Committing session initialization...")
            await self.db.commit()
            print("[DEBUG] Session initialization committed.")

        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        print(f"[DEBUG] Calling Interview Agent for greeting at {self.agent_url}...")
        greeting_text, is_end = await self._get_agent_response()
        print(f"[DEBUG] Interview Agent returned greeting: {greeting_text}")
        
        print("[DEBUG] Saving interviewer turn to transcript repo...")
        async with self.db_lock:
            await self.transcript_repo.append_turn(
                self.session_id,
                "interviewer",
                greeting_text
            )
        
        print("[DEBUG] Sending greeting to websocket...")
        await ws.send_text(json.dumps({"type": "tts_start", "text": greeting_text}))
        audio = await deepgram_tts_bytes(greeting_text)
        await ws.send_bytes(audio)
        await ws.send_text(json.dumps({"type": "tts_end"}))

        async def handle_final(full: str, confidence: Optional[float]):
            if self.is_completed:
                return
                
            print(f"[DEBUG] Received final transcript: {full}")
            await ws.send_text(json.dumps({
                "type": "final",
                "text": full,
                "confidence": confidence
            }))
            
            print("[DEBUG] Appending candidate turn to transcript repo...")
            async with self.db_lock:
                await self.transcript_repo.append_turn(
                    self.session_id,
                    "candidate",
                    full
                )
            
            print(f"[DEBUG] Calling Interview Agent for response to: {full}")
            llm_text, is_end = await self._get_agent_response(full)
            
            print(f"[DEBUG] Agent Response (is_end={is_end}): {llm_text}")
            
            async with self.db_lock:
                await self.transcript_repo.append_turn(
                    self.session_id,
                    "interviewer",
                    llm_text
                )
            
            await ws.send_text(json.dumps({"type": "tts_start", "text": llm_text}))
            audio = await deepgram_tts_bytes(llm_text)
            await ws.send_bytes(audio)
            await ws.send_text(json.dumps({"type": "tts_end"}))
            
            if is_end:
                await ws.send_text(json.dumps({"type": "session_completed"}))
                await self.complete_session(auto_evaluate=True)

        print("[DEBUG] Connecting to Deepgram STT...")
        await self.stt.connect(ws, handle_final)
        print("[DEBUG] Deepgram STT connected.")

    def write_audio(self, chunk: bytes):
        self.transcoder.write(chunk)

    async def on_disconnect(self):
        print(f"[DEBUG] Disconnect detected for session {self.session_id}")
        if not self.is_completed:
            await self.complete_session(auto_evaluate=False)

    def close(self):
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        self.transcoder.close()