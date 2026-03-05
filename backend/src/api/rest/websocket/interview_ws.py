from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.core.services.interview_service import InterviewService
import asyncio
from uuid import UUID, uuid4
from src.api.rest.dependencies import get_db

router = APIRouter()

@router.websocket("/ws/interview")
async def interview_ws(ws: WebSocket):
    await ws.accept()
    session_id_str = ws.query_params.get("session_id")
    assessment_id = ws.query_params.get("assessment_id")
    invitation_id_str = ws.query_params.get("invitation_id")
    
    session_id = UUID(session_id_str) if session_id_str else uuid4()
    invitation_id = UUID(invitation_id_str) if invitation_id_str else None
    
    if not session_id_str:
        print(f"Generated new session_id: {session_id}")
    
    if not assessment_id or assessment_id == "default_assessment":
        print("Warning: assessment_id not provided in query params, using default")
        assessment_id = "859f91cc-660d-4a1a-91a7-3238886a8e1d" 

    async for db in get_db():
        service = InterviewService(db, session_id, assessment_id, invitation_id)
        stt_task = asyncio.create_task(service.start(ws))
        try:
            while True:
                msg = await ws.receive()
                
                if msg.get("type") == "websocket.disconnect":
                    raise WebSocketDisconnect
                
                if msg.get("bytes"):
                    service.write_audio(msg["bytes"])
                    
        except WebSocketDisconnect:
            print(f"Websocket disconnected for session: {session_id}")
        finally:
            stt_task.cancel()
            await service.on_disconnect()
            service.close()
            break