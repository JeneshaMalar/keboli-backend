from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import uuid
from typing import List
from src.data.models.invitation import Invitation
from src.data.models.candidate import Candidate
from src.api.rest.dependencies import get_db, get_current_recruiter
from src.data.models.evaluation import Evaluation
from src.data.models.interview_session import InterviewSession
from src.data.models.transcript import Transcript
from src.data.models.assessment import Assessment
from src.schemas.evaluation_schema import EvaluationCreate, EvaluationResponse, EvaluationUpdate, EvaluationReportResponse
from src.data.models.recruiter import Recruiter
from src.constants.enums import InterviewSessionStatus, InvitationStatus
from sqlalchemy import update
from src.config.settings import settings

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

async def resolve_session_id(session_id: str, db: AsyncSession) -> uuid.UUID:
    try:
        return uuid.UUID(session_id)
    except (ValueError, TypeError):
        invitation = await db.scalar(select(Invitation).where(Invitation.token == session_id))
        if invitation:
            query = select(InterviewSession).where(InterviewSession.invitation_id == invitation.id).order_by(InterviewSession.created_at.desc())
            session = await db.scalar(query)
            if session:
                return session.id
    raise HTTPException(status_code=404, detail=f"Session or token '{session_id}' not found")

@router.get("/transcript/{session_id}")
async def get_transcript_for_eval(session_id: str, db: AsyncSession = Depends(get_db)):
    target_id = await resolve_session_id(session_id, db)
    transcript = await db.scalar(select(Transcript).where(Transcript.session_id == target_id))
    if not transcript:
        return []
    return transcript.full_transcript

@router.get("/session/{session_id}")
async def get_session_details_for_eval(session_id: str, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=404, detail="Session not found")
    
    session, assessment = row
    return {
        "id": str(session.id),
        "status": session.status,
        "assessment_id": str(assessment.id),
        "assessment_title": assessment.title,
        "job_description": assessment.job_description,
        "skill_graph": assessment.skill_graph,
        "passing_score": assessment.passing_score,
        "difficulty_level": assessment.difficulty_level.value if assessment.difficulty_level else "medium"
    }

@router.post("/report/{session_id}", response_model=EvaluationResponse)
async def post_evaluation_report(
    session_id: str, 
    payload: EvaluationCreate, 
    db: AsyncSession = Depends(get_db)
):
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
    
    existing = await db.scalar(select(Evaluation).where(Evaluation.session_id == target_id))
    
    if existing:
        for key, value in payload.model_dump().items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return existing
        
    evaluation = Evaluation(
        session_id=target_id,
        **payload.model_dump()
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation

@router.get("/report/{session_id}", response_model=EvaluationReportResponse)
async def get_evaluation_report(
    session_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    target_id = await resolve_session_id(session_id, db)
    evaluation = await db.scalar(select(Evaluation).where(Evaluation.session_id == target_id))
    transcript = await db.scalar(select(Transcript).where(Transcript.session_id == target_id))
    
    query = (
        select(InterviewSession, Candidate)
        .join(Invitation, InterviewSession.invitation_id == Invitation.id)
        .join(Candidate, Invitation.candidate_id == Candidate.id)
        .where(InterviewSession.id == target_id)
    )
    result = await db.execute(query)
    row = result.first()
    
    if not evaluation and not transcript and not row:
        raise HTTPException(status_code=404, detail="Interview session not found")
        
    session, candidate = row if row else (None, None)
            
    return {
        "evaluation": evaluation,
        "transcript": {
            "full_transcript": transcript.full_transcript if transcript else []
        },
        "candidate": {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "resume_url": getattr(candidate, 'resume_url', None)
        } if candidate else None
    }

@router.patch("/report/{session_id}", response_model=EvaluationResponse)
async def update_evaluation_report(
    session_id: str, 
    payload: EvaluationUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    target_id = await resolve_session_id(session_id, db)
    evaluation = await db.scalar(select(Evaluation).where(Evaluation.session_id == target_id))
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(evaluation, key, value)
    
    await db.commit()
    await db.refresh(evaluation)
    return evaluation

@router.post("/trigger/{session_id}")
async def trigger_evaluation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Recruiter = Depends(get_current_recruiter)
):
    target_id = await resolve_session_id(session_id, db)
    try:
        async with httpx.AsyncClient() as client:
            url = f"{settings.EVALUATION_SERVICE_URL}/api/v1/evaluate/{target_id}"
            response = await client.post(url, timeout=300.0)
            response.raise_for_status()
            return {"status": "success", "message": "Evaluation triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger evaluation: {str(e)}")
