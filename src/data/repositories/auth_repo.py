"""Repository for authentication and onboarding persistence operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.organization import Organization
from src.data.models.recruiter import Recruiter


class AuthRepository:
    """Data-access layer for authentication-related entities.

    Handles recruiter lookups, organization creation, and recruiter
    creation within the caller-supplied async session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_recruiter_by_email(self, email: str) -> Recruiter | None:
        """Look up a recruiter by email address.

        Args:
            email: The email to search for.

        Returns:
            The Recruiter if found, otherwise None.
        """
        query = select(Recruiter).where(Recruiter.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_organization(self, name: str) -> Organization:
        """Insert a new organization record.

        Args:
            name: Display name for the organization.

        Returns:
            The created Organization instance (flushed, not committed).
        """
        org = Organization(name=name)
        self.session.add(org)
        await self.session.flush()
        return org

    async def create_recruiter(
        self, org_id: uuid.UUID, email: str, password_hash: str, role: str
    ) -> Recruiter:
        """Insert a new recruiter record.

        Args:
            org_id: UUID of the organization the recruiter belongs to.
            email: Recruiter email address.
            password_hash: Bcrypt-hashed password.
            role: Role identifier (e.g. HIRING_MANAGER).

        Returns:
            The created Recruiter instance (added to session, not flushed).
        """
        recruiter = Recruiter(
            org_id=org_id, email=email, password_hash=password_hash, role=role
        )
        self.session.add(recruiter)
        return recruiter
