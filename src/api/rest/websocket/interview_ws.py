"""WebSocket handler for real-time AI interview sessions."""

import asyncio
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.rest.dependencies import get_db
from src.core.services.interview_service import InterviewService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/interview")
async def interview_ws(ws: WebSocket) -> None:
    """Handle a WebSocket connection for a real-time interview session.

    Manages the session lifecycle: accepts the connection, initializes
    the interview service, streams audio data, and cleans up on disconnect.

    Args:
        ws: The incoming WebSocket connection.
    """
    await ws.accept()
    session_id_str = ws.query_params.get("session_id")
    assessment_id = ws.query_params.get("assessment_id")
    invitation_id_str = ws.query_params.get("invitation_id")

    session_id = UUID(session_id_str) if session_id_str else uuid4()
    invitation_id = UUID(invitation_id_str) if invitation_id_str else None

    if not assessment_id or assessment_id == "default_assessment":
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
            logger.info("WebSocket disconnected for session: %s", session_id)
        finally:
            stt_task.cancel()
            await service.on_disconnect()
            service.close()
