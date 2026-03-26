"""Repository for assessment persistence operations."""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.assessment import Assessment


class AssessmentRepository:
    """Data-access layer for Assessment entities.

    Provides CRUD helpers that operate within the caller-supplied
    async session, deferring commit control to the service layer.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, assessment_data: dict[str, object]) -> Assessment:
        """Insert a new assessment record.

        Args:
            assessment_data: Column values for the new assessment.

        Returns:
            The created Assessment instance (flushed, not yet committed).
        """
        instance = Assessment(**assessment_data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, assessment_id: uuid.UUID) -> Assessment | None:
        """Fetch a single assessment by primary key.

        Args:
            assessment_id: UUID of the assessment.

        Returns:
            The Assessment if found, otherwise None.
        """
        return await self.session.get(Assessment, assessment_id)

    async def get_multi_by_org(self, org_id: uuid.UUID) -> list[Assessment]:
        """Retrieve all assessments belonging to an organization.

        Args:
            org_id: UUID of the organization.

        Returns:
            List of assessments for the organization.
        """
        query = select(Assessment).where(Assessment.org_id == org_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, assessment_id: uuid.UUID, **kwargs: object) -> Assessment:
        """Update an assessment's fields by primary key.

        Args:
            assessment_id: UUID of the assessment to update.
            **kwargs: Column-value pairs to set.

        Returns:
            The updated Assessment instance.
        """
        query = (
            update(Assessment)
            .where(Assessment.id == assessment_id)
            .values(**kwargs)
            .returning(Assessment)
        )
        result = await self.session.execute(query)
        return result.scalar_one()
