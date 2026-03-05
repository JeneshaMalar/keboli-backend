from fastapi import HTTPException, status
from src.data.repositories.assessment_repo import AssessmentRepository
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
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
        
        return assessment

    async def toggle_status(self, assessment_id: uuid.UUID, active_status: bool):
        assessment = await self.repo.get_by_id(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
            
        updated = await self.repo.update(assessment_id, is_active=active_status)
        await self.session.commit() 
        return updated