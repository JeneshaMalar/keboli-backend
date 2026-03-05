from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.data.models.assessment import Assessment
import uuid
class AssessmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, assessment_data: dict) -> Assessment:
        instance = Assessment(**assessment_data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, assessment_id: uuid.UUID) -> Assessment | None:
        return await self.session.get(Assessment, assessment_id)

    async def get_multi_by_org(self, org_id: uuid.UUID):
        query = select(Assessment).where(Assessment.org_id == org_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, assessment_id: uuid.UUID, **kwargs):
        query = update(Assessment).where(Assessment.id == assessment_id).values(**kwargs).returning(Assessment)
        result = await self.session.execute(query)
        return result.scalar_one()