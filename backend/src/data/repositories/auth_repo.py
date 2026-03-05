import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.data.models.organization import Organization
from src.data.models.recruiter import Recruiter

class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_recruiter_by_email(self, email: str) -> Recruiter | None:
        query = select(Recruiter).where(Recruiter.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_organization(self, name: str) -> Organization:
        org = Organization(name=name)
        self.session.add(org)
        await self.session.flush()
        return org

    async def create_recruiter(self, org_id: uuid.UUID, email: str, password_hash: str, role: str) -> Recruiter:
        recruiter = Recruiter(
            org_id=org_id,
            email=email,
            password_hash=password_hash,
            role=role
        )
        self.session.add(recruiter)
        return recruiter