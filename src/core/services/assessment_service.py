"""Assessment service for managing assessment lifecycle and external integrations."""

import asyncio
import logging
import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.exceptions import NotFoundError, ValidationError
from src.data.models.assessment import Assessment
from src.data.repositories.assessment_repo import AssessmentRepository

logger = logging.getLogger("assessment-service")


class AssessmentService:
    """Service layer for managing assessment lifecycle and external integrations.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AssessmentRepository(session)

    async def create_assessment(
        self, org_id: uuid.UUID, data: dict[str, object]
    ) -> Assessment:
        """Create a new assessment and trigger background skill graph generation.

        Args:
            org_id: Unique identifier of the organization creating the assessment.
            data: Dictionary containing assessment attributes (e.g., duration, title).

        Returns:
            The newly created assessment object.

        Raises:
            ValidationError: If duration_minutes is 0 or negative.
        """
        if data.get("duration_minutes", 0) <= 0:
            raise ValidationError(
                message="Duration must be greater than 0",
                field="duration_minutes",
            )

        data["org_id"] = org_id

        assessment = await self.repo.create(data)

        await self.session.commit()
        await self.session.refresh(assessment)

        assessment_id = str(assessment.id)
        asyncio.create_task(self._trigger_skill_graph_generation(assessment_id))

        return assessment

    async def _trigger_skill_graph_generation(self, assessment_id: str) -> None:
        """Fire-and-forget call to the interview agent to generate skill graph.

        Args:
            assessment_id: String representation of the assessment UUID.
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.INTERVIEW_AGENT_URL}/generate-skill-graph"
                response = await client.post(
                    url,
                    json={"assessment_id": assessment_id},
                    timeout=120.0,
                )
                if response.status_code == 200:
                    logger.info(f"Skill graph generated for assessment {assessment_id}")
                else:
                    logger.warning(
                        f"Skill graph generation returned {response.status_code} for {assessment_id}"
                    )
        except Exception as e:
            logger.error(
                f"Failed to trigger skill graph generation for {assessment_id}: {e}"
            )

    async def toggle_status(
        self, assessment_id: uuid.UUID, active_status: bool
    ) -> Assessment:
        """Update the activation status of an existing assessment.

        Args:
            assessment_id: UUID of the assessment to update.
            active_status: Whether the assessment should be active or inactive.

        Returns:
            The updated assessment object.

        Raises:
            NotFoundError: If the assessment_id does not exist in the database.
        """
        assessment = await self.repo.get_by_id(assessment_id)
        if not assessment:
            raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))

        updated = await self.repo.update(assessment_id, is_active=active_status)
        await self.session.commit()
        return updated
