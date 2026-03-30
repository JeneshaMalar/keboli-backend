"""Candidate service for managing candidate data and bulk operations."""

import csv
import io
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.data.models.candidate import Candidate
from src.data.repositories.candidate_repo import CandidateRepository
from src.schemas.candidate_schema import CandidateCreate

logger = logging.getLogger(__name__)


class CandidateService:
    """Service layer for managing candidate data, including single creation,
    bulk uploads, and organization-specific retrieval.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.repo = CandidateRepository(session)

    async def create_candidate(
        self, org_id: uuid.UUID, data: CandidateCreate
    ) -> Candidate:
        """Create a single candidate within an organization.

        Args:
            org_id: Unique identifier of the organization.
            data: Pydantic model containing candidate details (email, name, etc.).

        Returns:
            The newly created candidate object.

        Raises:
            ConflictError: If a candidate with the same email already exists in the org.
        """
        existing = await self.repo.get_by_email_and_org(data.email, org_id)
        if existing:
            raise ConflictError(
                message="Candidate with this email already exists in your organization"
            )

        candidate_data = data.model_dump()
        candidate_data["org_id"] = org_id

        candidate = await self.repo.create(candidate_data)
        return candidate

    async def get_org_candidates(self, org_id: uuid.UUID) -> list[Candidate]:
        """Retrieve all candidates belonging to a specific organization.

        Args:
            org_id: Unique identifier of the organization.

        Returns:
            A list of candidate objects.
        """
        return await self.repo.get_multi_by_org(org_id)

    async def delete_candidate(
        self, org_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> dict[str, str]:
        """Remove a candidate from the system.

        Args:
            org_id: Organization ID to ensure the user has permission to delete.
            candidate_id: Unique identifier of the candidate to remove.

        Returns:
            A success message dictionary.

        Raises:
            NotFoundError: If the candidate is not found or doesn't belong to the org.
        """
        candidate = await self.repo.get_by_id(candidate_id)
        if not candidate or candidate.org_id != org_id:
            raise NotFoundError(resource="Candidate", resource_id=str(candidate_id))

        await self.repo.delete(candidate_id)
        return {"message": "Candidate deleted successfully"}

    async def bulk_upload_candidates(
        self, org_id: uuid.UUID, file_content: bytes, filename: str
    ) -> dict[str, Any]:
        """Process CSV content to create multiple candidates at once.

        Args:
            org_id: Unique identifier of the organization.
            file_content: Raw bytes of the uploaded CSV file.
            filename: Original filename for format validation.

        Returns:
            A dictionary containing the count of created records and a list of errors.

        Raises:
            ValidationError: If the file format is invalid.
        """
        if not filename or not filename.endswith(".csv"):
            raise ValidationError(
                message="Only CSV files are supported for bulk upload",
                field="file",
            )

        try:
            decoded = file_content.decode("utf-8-sig")
            f = io.StringIO(decoded)
            reader = csv.DictReader(f)

            candidates_to_create: list[dict[str, object]] = []
            errors: list[str] = []

            for row_num, row in enumerate(reader, 1):
                row_data = {k.lower().strip(): v for k, v in row.items() if k}

                email = row_data.get("email")
                name = row_data.get("name") or row_data.get("full name")

                if not email or not name:
                    if not any(row_data.values()):
                        continue
                    errors.append(
                        f"Row {row_num}: Missing email or name. "
                        f"(Fields found: {list(row_data.keys())})"
                    )
                    continue

                email = str(email).strip()
                name = str(name).strip()

                existing = await self.repo.get_by_email_and_org(email, org_id)
                if existing:
                    errors.append(
                        f"Row {row_num}: Candidate with email {email} already exists"
                    )
                    continue

                if any(c["email"] == email for c in candidates_to_create):
                    errors.append(
                        f"Row {row_num}: Duplicate email {email} found in CSV file"
                    )
                    continue

                candidates_to_create.append(
                    {
                        "email": email,
                        "name": name,
                        "org_id": org_id,
                    }
                )

            if candidates_to_create:
                created = await self.repo.create_bulk(candidates_to_create)
                return {"created_count": len(created), "errors": errors}
            else:
                return {"created_count": 0, "errors": errors}
        except ValidationError:
            raise
        except UnicodeDecodeError as e:
            raise ValidationError(
                message=f"File encoding error: {e!s}"
            ) from e
        except Exception as e:
            logger.error("Bulk upload failed for org %s: %s", org_id, e)
            raise ValidationError(message=f"Bulk upload failed: {e!s}") from e
