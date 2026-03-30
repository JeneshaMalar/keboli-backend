"""LiveKit WebRTC session routes for interview token generation and lifecycle management."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.core.services.livekit_service import LiveKitService
from src.core.services.invitation_service import InvitationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/livekit", tags=["livekit"])


class TokenRequest(BaseModel):
    """Request schema for LiveKit token generation."""

    session_id: uuid.UUID | None = None
    invitation_id: uuid.UUID | None = None
    assessment_id: uuid.UUID | None = None
    invitation_token: str | None = None


class HeartbeatRequest(BaseModel):
    """Request schema for session heartbeat updates."""

    session_id: uuid.UUID
    remaining_seconds: int | None = None


class SessionCompleteRequest(BaseModel):
    """Request schema for marking a session as completed."""

    session_id: uuid.UUID


class SessionUpdateRequest(BaseModel):
    """Request schema for updating session fields."""

    session_id: uuid.UUID
    egress_id: str | None = None
    refresh_count: int | None = None


@router.post(
    "/token",
    response_model=dict,
    summary="Generate LiveKit token",
    description="Generate or retrieve a LiveKit session token with room access grants.",
)
async def get_token(
    invitation_token: str | None = None,
    payload: TokenRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate a LiveKit access token for a session room.

    Creates a new interview session if one doesn't exist, resolving
    assessment duration from invitations or assessments.

    Args:
        invitation_token: Optional token from query params (legacy/convenience).
        payload: Token request containing session/invitation/assessment IDs.
        db: Async database session.

    Returns:
        Dictionary with session metadata and LiveKit token.
    """
    session_id = uuid.uuid4()
    inv_id = None
    ass_id = None

    if payload:
        session_id = payload.session_id or session_id
        inv_id = payload.invitation_id
        ass_id = payload.assessment_id
        if not invitation_token:
            invitation_token = payload.invitation_token

    if invitation_token and not inv_id:

        inv_service = InvitationService(db)
        try:
            invitation = await inv_service.validate_token(invitation_token)
            inv_id = invitation.id
        except Exception as e:
            logger.warning(f"Failed to resolve invitation token {invitation_token}: {e}")

    service = LiveKitService(db)
    return await service.get_or_create_session(
        session_id=session_id,
        invitation_id=inv_id,
        assessment_id=ass_id,
    )


@router.post(
    "/heartbeat",
    response_model=dict,
    summary="Session heartbeat",
    description="Update session heartbeat timestamp and optionally sync remaining time.",
)
async def heartbeat(
    payload: HeartbeatRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Update the session heartbeat and remaining time.

    Args:
        payload: Heartbeat request with session ID and optional remaining seconds.
        db: Async database session.

    Returns:
        Status confirmation.
    """
    service = LiveKitService(db)
    return await service.update_heartbeat(
        session_id=payload.session_id,
        remaining_seconds=payload.remaining_seconds,
    )


@router.post(
    "/complete",
    response_model=dict,
    summary="Complete session",
    description="Mark an interview session as completed and update invitation status.",
)
async def complete_session(
    payload: SessionCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Mark an interview session as completed.

    Args:
        payload: Request containing the session ID to complete.
        db: Async database session.

    Returns:
        Status confirmation with session ID.
    """
    service = LiveKitService(db)
    return await service.complete_session(session_id=payload.session_id)


class TranscriptAppendRequest(BaseModel):
    """Request schema for appending a transcript turn."""

    role: str
    content: str


@router.get(
    "/transcript/{session_id}",
    response_model=dict,
    summary="Get transcript",
    description="Retrieve the full interview transcript for a session.",
)
async def get_transcript(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve the interview transcript for a given session.

    Args:
        session_id: UUID of the interview session.
        db: Async database session.

    Returns:
        Dictionary with transcript data.
    """
    service = LiveKitService(db)
    return await service.get_transcript(session_id=session_id)


@router.post(
    "/transcript/{session_id}/append",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Append transcript",
    description="Append a new conversation turn (interviewer/candidate) to the session transcript.",
)
async def append_transcript(
    session_id: uuid.UUID,
    payload: TranscriptAppendRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Append a new conversational turn to the session transcript.

    Args:
        session_id: UUID of the interview session.
        payload: Conversation turn containing role and content.
        db: Async database session.

    Returns:
        Status confirmation.
    """
    service = LiveKitService(db)
    return await service.append_transcript(
        session_id=session_id,
        role=payload.role,
        content=payload.content,
    )


@router.get(
    "/session/{session_id}",
    response_model=dict,
    summary="Get session details",
    description="Retrieve full session and linked assessment details for evaluation.",
)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve interview session and assessment data.

    Args:
        session_id: UUID of the interview session.
        db: Async database session.

    Returns:
        Dictionary with session metadata and assessment details.
    """
    service = LiveKitService(db)
    return await service.get_session_field(session_id=session_id)


@router.post(
    "/session/update",
    response_model=dict,
    summary="Update session",
    description="Update session fields such as egress_id or refresh_count.",
)
async def update_session(
    payload: SessionUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Update session metadata fields (egress ID, refresh count).

    Args:
        payload: Request with session ID and fields to update.
        db: Async database session.

    Returns:
        Status confirmation.
    """
    update_fields: dict[str, Any] = {}
    if payload.egress_id is not None:
        update_fields["egress_id"] = payload.egress_id
    if payload.refresh_count is not None:
        update_fields["refresh_count"] = payload.refresh_count

    if not update_fields:
        return {"status": "no_changes"}

    service = LiveKitService(db)
    return await service.update_session_field(
        session_id=payload.session_id,
        **update_fields,
    )
