from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from src.data.models.candidate import Candidate
import uuid
from typing import List, Optional

class CandidateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, candidate_data: dict) -> Candidate:
        instance = Candidate(**candidate_data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def create_bulk(self, candidates_data: List[dict]) -> List[Candidate]:
        instances = [Candidate(**data) for data in candidates_data]
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    async def get_by_id(self, candidate_id: uuid.UUID) -> Optional[Candidate]:
        return await self.session.get(Candidate, candidate_id)

    async def get_by_email_and_org(self, email: str, org_id: uuid.UUID) -> Optional[Candidate]:
        query = select(Candidate).where(Candidate.email == email, Candidate.org_id == org_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_by_org(self, org_id: uuid.UUID) -> List[Candidate]:
        query = select(Candidate).where(Candidate.org_id == org_id).order_by(Candidate.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, candidate_id: uuid.UUID, **kwargs) -> Candidate:
        query = update(Candidate).where(Candidate.id == candidate_id).values(**kwargs).returning(Candidate)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def delete(self, candidate_id: uuid.UUID):
        query = delete(Candidate).where(Candidate.id == candidate_id)
        await self.session.execute(query)
