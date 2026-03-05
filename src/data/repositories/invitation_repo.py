from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from src.data.models.invitation import Invitation
import uuid
from typing import List, Optional
from src.data.models.candidate import Candidate
from sqlalchemy.orm import joinedload, selectinload

class InvitationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, invitation_data: dict) -> Invitation:
        instance = Invitation(**invitation_data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, invitation_id: uuid.UUID) -> Optional[Invitation]:
        query = (
            select(Invitation)
            .where(Invitation.id == invitation_id)
            .options(joinedload(Invitation.candidate), joinedload(Invitation.assessment))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> Optional[Invitation]:
        query = (
            select(Invitation)
            .where(Invitation.token == token)
            .options(joinedload(Invitation.candidate), joinedload(Invitation.assessment))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_by_org(self, org_id: uuid.UUID) -> List[Invitation]:
        from src.data.models.interview_session import InterviewSession
        query = (
            select(Invitation)
            .join(Candidate)
            .where(Candidate.org_id == org_id)
            .options(
                joinedload(Invitation.candidate),
                selectinload(Invitation.sessions).selectinload(InterviewSession.evaluation)
            )
            .order_by(Invitation.sent_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, invitation_id: uuid.UUID, **kwargs) -> Invitation:
        query = update(Invitation).where(Invitation.id == invitation_id).values(**kwargs).returning(Invitation)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def delete(self, invitation_id: uuid.UUID):
        query = delete(Invitation).where(Invitation.id == invitation_id)
        await self.session.execute(query)
