import asyncio
import logging
from fastapi import HTTPException, status
from src.data.repositories.assessment_repo import AssessmentRepository
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import httpx
from src.config.settings import settings

logger = logging.getLogger("assessment-service")

class AssessmentService:
    def __init__(self, session: AsyncSession):
        self.session = session 
        self.repo = AssessmentRepository(session)

    async def create_assessment(self, org_id: uuid.UUID, data: dict):
        if data.get("duration_minutes", 0) <= 0:
            raise HTTPException(status_code=400, detail="Duration must be greater than 0")
        
        data["org_id"] = org_id
        
        assessment = await self.repo.create(data)
        
        await self.session.commit()
        
        await self.session.refresh(assessment)
        
        # Trigger skill graph generation in the background via the interview agent
        assessment_id = str(assessment.id)
        asyncio.create_task(self._trigger_skill_graph_generation(assessment_id))
        
        return assessment

    async def _trigger_skill_graph_generation(self, assessment_id: str):
        """Fire-and-forget call to the interview agent to generate skill graph."""
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
                    logger.warning(f"Skill graph generation returned {response.status_code} for {assessment_id}")
        except Exception as e:
            logger.error(f"Failed to trigger skill graph generation for {assessment_id}: {e}")

    async def toggle_status(self, assessment_id: uuid.UUID, active_status: bool):
        assessment = await self.repo.get_by_id(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
            
        updated = await self.repo.update(assessment_id, is_active=active_status)
        await self.session.commit() 
        return updated