from fastapi import APIRouter, HTTPException, Query, Depends
from livekit import api as livekit_api
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.api.rest.dependencies import get_db
from src.config.settings import settings
from src.data.models.invitation import Invitation
from src.data.models.interview_session import InterviewSession
from src.constants.enums import InterviewSessionStatus, InvitationStatus
from src.data.repositories.interview_transcript_repo import InterviewTranscriptRepository
from datetime import datetime
from pydantic import BaseModel
import httpx
import asyncio
import logging

from sqlalchemy.orm import joinedload

logger = logging.getLogger("livekit-routes")
from src.data.database.session import AsyncSessionLocal

router = APIRouter(prefix="/livekit", tags=["livekit"])

class TranscriptAppend(BaseModel):
    role: str
    content: str


async def _start_room_recording(room_name: str, session_id: str):
    api_key = settings.LIVEKIT_API_KEY
    api_secret = settings.LIVEKIT_API_SECRET
    livekit_url = settings.LIVEKIT_URL

    if not api_key or not api_secret or not livekit_url:
        logger.warning("LiveKit credentials not configured — skipping recording")
        return

    api_url = livekit_url.replace("wss://", "https://")
    lkapi = livekit_api.LiveKitAPI(api_url, api_key, api_secret)

    try:
        # poll for room existence (wait up to 60 seconds)
        room_found = False
        for _ in range(30):
            rooms = await lkapi.room.list_rooms(livekit_api.ListRoomsRequest())
            if any(r.name == room_name for r in rooms.rooms):
                room_found = True
                break
            await asyncio.sleep(2)

        if not room_found:
             logger.warning(f"Room {room_name} not found after timeout — skipping recording start")
             return

        req = livekit_api.RoomCompositeEgressRequest(
            room_name=room_name,
            layout="grid",
            audio_only=False,
            file_outputs=[
        livekit_api.EncodedFileOutput(
            filepath=f"{room_name}/{session_id}.mp4",
            file_type=livekit_api.EncodedFileType.MP4
        )
    ]
        )

        egress_info = await lkapi.egress.start_room_composite_egress(req)
        egress_id = egress_info.egress_id

        logger.info(f"Started recording for room {room_name}, egress_id={egress_id}")

        async with AsyncSessionLocal() as db:
            query = (
                update(InterviewSession)
                .where(InterviewSession.id == UUID(session_id))
                .values(egress_id=egress_id)
            )

            await db.execute(query)
            await db.commit()

    except Exception as e:
        logger.error(f"Failed to start recording for room {room_name}: {e}", exc_info=True)

    finally:
        await lkapi.aclose()


async def _stop_room_recording(egress_id: str):
    api_key = settings.LIVEKIT_API_KEY
    api_secret = settings.LIVEKIT_API_SECRET
    livekit_url = settings.LIVEKIT_URL

    if not api_key or not api_secret or not livekit_url:
        return

    try:
        api_url = livekit_url.replace("wss://", "https://")
        lkapi = livekit_api.LiveKitAPI(api_url, api_key, api_secret)

        await lkapi.egress.stop_egress(livekit_api.StopEgressRequest(egress_id=egress_id))
        logger.info(f"Stopped recording egress_id={egress_id}")

        await lkapi.aclose()

    except Exception as e:
        logger.warning(f"Failed to stop recording egress_id={egress_id}: {e}")


@router.post("/token")
async def get_token(
    invitation_token: str = Query(..., description="The invitation token"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Invitation).options(joinedload(Invitation.assessment)).where(Invitation.token == invitation_token)
    result = await db.execute(query)
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status == InvitationStatus.SENT:
        invitation.status = InvitationStatus.CLICKED
        await db.commit()

  
    query = select(InterviewSession).where(
        InterviewSession.invitation_id == invitation.id,
        InterviewSession.status == InterviewSessionStatus.IN_PROGRESS
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        duration_mins = 60
        if invitation.assessment:
            duration_mins = invitation.assessment.duration_minutes

        session = InterviewSession(
            id=uuid4(),
            invitation_id=invitation.id,
            candidate_id=invitation.candidate_id,
            status=InterviewSessionStatus.IN_PROGRESS,
            remaining_seconds=duration_mins * 60,
            started_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
    
    room_name = f"room_{session.id}_{invitation.assessment_id}"
    participant_identity = f"candidate_{session.id.hex[:8]}"

    livekit_url = settings.LIVEKIT_URL
    api_key = settings.LIVEKIT_API_KEY
    api_secret = settings.LIVEKIT_API_SECRET

    if not api_key or not api_secret:
         raise HTTPException(status_code=500, detail="LiveKit credentials not configured")

    try:
        token = livekit_api.AccessToken(api_key, api_secret) \
            .with_identity(participant_identity) \
            .with_name("Candidate") \
            .with_grants(livekit_api.VideoGrants(
                room_join=True,
                room=room_name,
            ))
        
      
        if not session.egress_id:
            asyncio.create_task(
                _start_room_recording(room_name, str(session.id))
            )
        
        return {
            "token": token.to_jwt(),
            "url": livekit_url,
            "room_name": room_name,
            "session_id": str(session.id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate LiveKit token: {str(e)}")

@router.post("/transcript/{session_id}/append")
async def append_transcript(
    session_id: UUID,
    payload: TranscriptAppend,
    db: AsyncSession = Depends(get_db)
):
    repo = InterviewTranscriptRepository(db)
    await repo.append_turn(session_id, payload.role, payload.content)
    return {"status": "success"}

@router.post("/session/{session_id}/complete")
async def complete_session(
    session_id: UUID,
    auto_evaluate: bool = True,
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(InterviewSession, session_id)
    egress_id = session.egress_id if session else None

    query = (
        update(InterviewSession)
        .where(InterviewSession.id == session_id)
        .values(status=InterviewSessionStatus.COMPLETED, completed_at=datetime.utcnow())
    )
    await db.execute(query)
    await db.commit()

    if egress_id:
        asyncio.create_task(_stop_room_recording(egress_id))

    if auto_evaluate:
        try:
            async with httpx.AsyncClient() as client:
                url = f"http://localhost:8002/api/v1/evaluate/{session_id}"
                await client.post(url, timeout=300.0)
        except Exception as e:
            print(f"Failed to trigger evaluation agent: {e}")

    return {"status": "success"}

@router.post("/session/heartbeat/{session_id}")
async def heartbeat(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    query = (
        update(InterviewSession)
        .where(InterviewSession.id == session_id)
        .values(
            last_heartbeat=datetime.utcnow(),
            remaining_seconds=InterviewSession.remaining_seconds - 5
        )
    )
    await db.execute(query)
    await db.commit()
    return {"status": "success"}