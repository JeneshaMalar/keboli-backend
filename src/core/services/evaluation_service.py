"""Evaluation service for managing evaluation reports and session data retrieval."""

import logging
import uuid
from typing import Any

import httpx
from src.config.settings import settings
from src.core.exceptions import AppError, NotFoundError
from src.data.models.evaluation import Evaluation
from src.data.repositories.evaluation_repo import EvaluationRepository

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service layer for evaluation report retrieval, external triggering,
    and admin overrides.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: Any) -> None:
        self.repo = EvaluationRepository(session)

    async def trigger_evaluation(self, session_id: uuid.UUID) -> dict[str, str]:
        """Trigger the external evaluation service for a completed interview.

        Args:
            session_id: UUID of the interview session to evaluate.

        Returns:
            A dictionary containing the evaluation status and session ID.

        Raises:
            AppError: If the external service call fails.
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.EVALUATION_SERVICE_URL}/api/v1/evaluate/{session_id}"
                response = await client.post(url, timeout=300.0)
                response.raise_for_status()
                return {"status": "triggered", "session_id": str(session_id)}
        except httpx.HTTPStatusError as e:
            logger.error(
                "Evaluation service returned error for session %s: %s",
                session_id,
                e.response.status_code,
            )
            raise AppError(
                message=f"Evaluation service returned {e.response.status_code}",
                status_code=502,
                error_code="EVALUATION_SERVICE_ERROR",
            ) from e
        except httpx.RequestError as e:
            logger.error(
                "Failed to connect to evaluation service for session %s: %s",
                session_id,
                e,
            )
            raise AppError(
                message="Failed to connect to evaluation service",
                status_code=502,
                error_code="EVALUATION_SERVICE_UNREACHABLE",
            ) from e

    async def save_evaluation(
        self,
        session_id: uuid.UUID,
        evaluation_data: dict[str, Any],
    ) -> Evaluation:
        """Persist or update an evaluation report from the external service.

        Args:
            session_id: UUID of the interview session.
            evaluation_data: Evaluation scores and metadata.

        Returns:
            The persisted Evaluation instance.

        Raises:
            AppError: If saving or updating the evaluation fails.
        """
        try:
            return await self.repo.save(session_id, evaluation_data)
        except Exception as e:
            logger.error("Failed to save evaluation for session %s: %s", session_id, e)
            raise AppError(
                message=f"Failed to save evaluation: {e!s}",
                status_code=500,
                error_code="EVALUATION_SAVE_FAILED",
            ) from e

    async def get_evaluation_by_session(
        self, session_id: uuid.UUID
    ) -> Evaluation | None:
        """Retrieve an evaluation by its associated session ID.

        Args:
            session_id: UUID of the interview session.

        Returns:
            The Evaluation if found, otherwise None.
        """
        return await self.repo.get_by_session(session_id)

    async def get_evaluation_report(
        self, session_id: uuid.UUID, org_id: uuid.UUID
    ) -> dict[str, Any]:
        """Build a full evaluation report with candidate and transcript data.

        Verifies that the session belongs to the requesting organization
        via the invitation → candidate → org chain.

        Args:
            session_id: UUID of the interview session.
            org_id: UUID of the requesting organization (for authorization).

        Returns:
            A dictionary containing the evaluation, transcript, and candidate data.

        Raises:
            NotFoundError: If the session or related data is not found.
        """
        interview_session = await self.repo.get_session_with_relations(session_id)

        if not interview_session:
            raise NotFoundError(resource="InterviewSession", resource_id=str(session_id))

        evaluation_data = None
        if interview_session.evaluation:
            ev = interview_session.evaluation
            evaluation_data = {
                "id": str(ev.id),
                "session_id": str(ev.session_id),
                "technical_score": float(ev.technical_score) if ev.technical_score else None,
                "communication_score": float(ev.communication_score) if ev.communication_score else None,
                "confidence_score": float(ev.confidence_score) if ev.confidence_score else None,
                "cultural_alignment_score": float(ev.cultural_alignment_score) if ev.cultural_alignment_score else None,
                "total_score": float(ev.total_score) if ev.total_score else None,
                "score_breakdown": ev.score_breakdown,
                "ai_summary": ev.ai_summary,
                "hiring_recommendation": ev.hiring_recommendation.value if ev.hiring_recommendation else None,
                "ai_explanation": ev.ai_explanation,
                "admin_recommendation": ev.admin_recommendation.value if ev.admin_recommendation else None,
                "admin_notes": ev.admin_notes,
                "is_tie_winner": ev.is_tie_winner,
                "detailed_analysis": ev.detailed_analysis,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
            }

        transcript_data = None
        if interview_session.transcript:
            tr = interview_session.transcript
            transcript_data = {
                "session_id": str(tr.session_id),
                "full_transcript": tr.full_transcript,
                "turn_count": tr.turn_count,
            }

        candidate_data = None
        if interview_session.invitation and interview_session.invitation.candidate:
            c = interview_session.invitation.candidate
            candidate_data = {
                "id": str(c.id),
                "email": c.email,
                "name": c.name,
            }

        return {
            "evaluation": evaluation_data,
            "transcript": transcript_data,
            "candidate": candidate_data,
        }

    async def update_admin_decision(
        self,
        session_id: uuid.UUID,
        update_data: dict[str, Any],
    ) -> Evaluation:
        """Apply admin overrides (recommendation, notes, tie-winner) to an evaluation.

        Args:
            session_id: UUID of the interview session.
            update_data: Dictionary of fields to update.

        Returns:
            The updated Evaluation instance.

        Raises:
            NotFoundError: If no evaluation exists for the session.
        """
        evaluation = await self.repo.update_decision(session_id, update_data)
        if not evaluation:
            raise NotFoundError(resource="Evaluation", resource_id=str(session_id))
        return evaluation

    async def get_org_evaluations(
        self, org_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """Retrieve all evaluations for an organization with candidate data.

        Args:
            org_id: UUID of the organization.

        Returns:
            List of evaluation summary dictionaries.
        """
        sessions = await self.repo.get_org_evaluations(org_id)

        evaluations = []
        for s in sessions:
            if not s.evaluation:
                continue
            ev = s.evaluation
            entry: dict[str, Any] = {
                "session_id": str(s.id),
                "status": s.status.value if s.status else None,
                "total_score": float(ev.total_score) if ev.total_score else None,
                "hiring_recommendation": ev.hiring_recommendation.value if ev.hiring_recommendation else None,
                "admin_recommendation": ev.admin_recommendation.value if ev.admin_recommendation else None,
                "is_tie_winner": ev.is_tie_winner,
            }
            if s.invitation and s.invitation.candidate:
                entry["candidate_name"] = s.invitation.candidate.name
                entry["candidate_email"] = s.invitation.candidate.email
            if s.invitation and s.invitation.assessment:
                entry["assessment_title"] = s.invitation.assessment.title
            evaluations.append(entry)

        return evaluations
