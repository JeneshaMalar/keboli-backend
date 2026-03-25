"""Evaluation routes for managing interview evaluation reports and transcripts."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.config.settings import settings
from src.constants.enums import InterviewSessionStatus, InvitationStatus
from src.core.exceptions import ExternalServiceError, NotFoundError
from src.data.models.assessment import Assessment
from src.data.models.candidate import Candidate
from src.data.models.evaluation import Evaluation
from src.data.models.interview_session import InterviewSession
from src.data.models.invitation import Invitation
from src.data.models.recruiter import Recruiter
from src.data.models.transcript import Transcript
from src.schemas.evaluation_schema import (
    EvaluationCreate,
    EvaluationReportResponse,
    EvaluationResponse,
    EvaluationUpdate,
)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class SessionDetailsResponse(BaseModel):
    """Response model for session details used by the evaluation agent."""

    id: str
    status: str
    assessment_id: str
    assessment_title: str
    job_description: str
    skill_graph: dict[str, object] | None
    passing_score: int
    difficulty_level: str


class TriggerResponse(BaseModel):
    """Response model for evaluation trigger endpoint."""

    status: str
    message: str


async def resolve_session_id(session_id: str, db: AsyncSession) -> uuid.UUID:
    """Resolve a session identifier which may be a UUID or an invitation token.

    Args:
        session_id: Either a UUID string or an invitation token.
        db: Async database session.

    Returns:
        The resolved UUID of the interview session.

    Raises:
        NotFoundError: If the session cannot be resolved.
    """
    try:
        return uuid.UUID(session_id)
    except (ValueError, TypeError):
        invitation = await db.scalar(
            select(Invitation).where(Invitation.token == session_id)
        )
        if invitation:
            query = (
                select(InterviewSession)
                .where(InterviewSession.invitation_id == invitation.id)
                .order_by(InterviewSession.created_at.desc())
            )
            session = await db.scalar(query)
            if session:
                return session.id
    raise NotFoundError(resource="Session", resource_id=session_id)


@router.get(
    "/transcript/{session_id}",
    summary="Get transcript for evaluation",
    description="Retrieve the full interview transcript for a given session.",
)
async def get_transcript_for_eval(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, str]]:
    """Retrieve the interview transcript for evaluation.

    Args:
        session_id: UUID or invitation token of the session.
        db: Async database session.

    Returns:
        List of transcript entries (role + content dicts).
    """
    target_id = await resolve_session_id(session_id, db)
    transcript = await db.scalar(
        select(Transcript).where(Transcript.session_id == target_id)
    )
    if not transcript:
        return []
    return transcript.full_transcript


@router.get(
    "/session/{session_id}",
    response_model=SessionDetailsResponse,
    summary="Get session details for evaluation",
    description="Retrieve session and assessment metadata needed by the evaluation agent.",
)
async def get_session_details_for_eval(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionDetailsResponse:
    """Retrieve session and linked assessment details for the evaluation agent.

    Args:
        session_id: UUID or invitation token of the session.
        db: Async database session.

    Returns:
        SessionDetailsResponse with assessment metadata.

    Raises:
        NotFoundError: If the session is not found.
    """
    target_id = await resolve_session_id(session_id, db)
    query = (
        select(InterviewSession, Assessment)
        .join(Invitation, InterviewSession.invitation_id == Invitation.id)
        .join(Assessment, Invitation.assessment_id == Assessment.id)
        .where(InterviewSession.id == target_id)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        raise NotFoundError(resource="Session", resource_id=session_id)

    session, assessment = row
    return SessionDetailsResponse(
        id=str(session.id),
        status=session.status.value
        if hasattr(session.status, "value")
        else str(session.status),
        assessment_id=str(assessment.id),
        assessment_title=assessment.title,
        job_description=assessment.job_description,
        skill_graph=assessment.skill_graph,
        passing_score=assessment.passing_score,
        difficulty_level=assessment.difficulty_level.value
        if assessment.difficulty_level
        else "medium",
    )


@router.post(
    "/report/{session_id}",
    response_model=EvaluationResponse,
    summary="Submit evaluation report",
    description="Create or update an evaluation report for a completed interview session.",
)
async def post_evaluation_report(
    session_id: str,
    payload: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
) -> Evaluation:
    """Create or update an evaluation report for a session.

    Args:
        session_id: UUID or invitation token of the session.
        payload: Evaluation scores, summary, and recommendation.
        db: Async database session.

    Returns:
        The created or updated evaluation record.
    """
    target_id = await resolve_session_id(session_id, db)
    session = await db.get(InterviewSession, target_id)
    if session and session.status != InterviewSessionStatus.COMPLETED:
        await db.execute(
            update(InterviewSession)
            .where(InterviewSession.id == target_id)
            .values(status=InterviewSessionStatus.COMPLETED)
        )
        if session.invitation_id:
            await db.execute(
                update(Invitation)
                .where(Invitation.id == session.invitation_id)
                .values(status=InvitationStatus.COMPLETED)
            )

    existing = await db.scalar(
        select(Evaluation).where(Evaluation.session_id == target_id)
    )

    if existing:
        for key, value in payload.model_dump().items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return existing

    evaluation = Evaluation(session_id=target_id, **payload.model_dump())
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


@router.get(
    "/report/{session_id}",
    response_model=EvaluationReportResponse,
    summary="Get full evaluation report",
    description="Retrieve the evaluation, transcript, and candidate info for a session.",
)
async def get_evaluation_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> EvaluationReportResponse:
    """Retrieve the full evaluation report including transcript and candidate info.

    Args:
        session_id: UUID or invitation token of the session.
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        EvaluationReportResponse with evaluation, transcript, and candidate data.

    Raises:
        NotFoundError: If the session is not found.
    """
    target_id = await resolve_session_id(session_id, db)
    evaluation = await db.scalar(
        select(Evaluation).where(Evaluation.session_id == target_id)
    )
    transcript = await db.scalar(
        select(Transcript).where(Transcript.session_id == target_id)
    )

    query = (
        select(InterviewSession, Candidate)
        .join(Invitation, InterviewSession.invitation_id == Invitation.id)
        .join(Candidate, Invitation.candidate_id == Candidate.id)
        .where(InterviewSession.id == target_id)
    )
    result = await db.execute(query)
    row = result.first()

    if not evaluation and not transcript and not row:
        raise NotFoundError(resource="Interview session", resource_id=session_id)

    session, candidate = row if row else (None, None)
    return EvaluationReportResponse(
        evaluation=evaluation,
        transcript={
            "full_transcript": transcript.full_transcript if transcript else []
        },
        candidate={
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "resume_url": getattr(candidate, "resume_url", None),
        }
        if candidate
        else None,
    )


@router.patch(
    "/report/{session_id}",
    response_model=EvaluationResponse,
    summary="Update evaluation report",
    description="Update admin recommendation, notes, or tie-winner status on an evaluation.",
)
async def update_evaluation_report(
    session_id: str,
    payload: EvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> Evaluation:
    """Update an existing evaluation with admin overrides.

    Args:
        session_id: UUID or invitation token of the session.
        payload: Fields to update (admin_recommendation, admin_notes, is_tie_winner).
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        The updated evaluation record.

    Raises:
        NotFoundError: If the evaluation is not found.
    """
    target_id = await resolve_session_id(session_id, db)
    evaluation = await db.scalar(
        select(Evaluation).where(Evaluation.session_id == target_id)
    )
    if not evaluation:
        raise NotFoundError(resource="Evaluation", resource_id=session_id)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(evaluation, key, value)

    await db.commit()
    await db.refresh(evaluation)
    return evaluation


@router.post(
    "/trigger/{session_id}",
    response_model=TriggerResponse,
    summary="Trigger evaluation processing",
    description="Manually trigger the evaluation agent for a completed interview session.",
)
async def trigger_evaluation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter),
) -> TriggerResponse:
    """Manually trigger evaluation processing for a session.

    Args:
        session_id: UUID or invitation token of the session.
        db: Async database session.
        current_user: Authenticated recruiter.

    Returns:
        TriggerResponse confirming the evaluation was triggered.

    Raises:
        ExternalServiceError: If the evaluation service call fails.
    """
    import httpx

    target_id = await resolve_session_id(session_id, db)
    try:
        async with httpx.AsyncClient() as client:
            url = f"{settings.EVALUATION_SERVICE_URL}/api/v1/evaluate/{target_id}"
            response = await client.post(url, timeout=300.0)
            response.raise_for_status()
            return TriggerResponse(status="success", message="Evaluation triggered")
    except Exception as e:
        raise ExternalServiceError(
            service_name="evaluation-agent",
            message=f"Failed to trigger evaluation: {e!s}",
        ) from e
