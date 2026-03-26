"""LiveKit WebRTC session routes for interview token generation and lifecycle management."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.core.services.livekit_service import LiveKitService
from src.data.models.recruiter import Recruiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/livekit", tags=["livekit"])


class TokenRequest(BaseModel):
    """Request schema for LiveKit token generation."""

    session_id: uuid.UUID | None = None
    invitation_id: uuid.UUID | None = None
    assessment_id: uuid.UUID | None = None


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
    payload: TokenRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate a LiveKit access token for a session room.

    Creates a new interview session if one doesn't exist, resolving
    assessment duration from invitations or assessments.

    Args:
        payload: Token request containing session/invitation/assessment IDs.
        db: Async database session.

    Returns:
        Dictionary with session metadata and LiveKit token.
    """
    session_id = payload.session_id or uuid.uuid4()
    service = LiveKitService(db)
    return await service.get_or_create_session(
        session_id=session_id,
        invitation_id=payload.invitation_id,
        assessment_id=payload.assessment_id,
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
