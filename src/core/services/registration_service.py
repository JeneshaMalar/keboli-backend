"""Registration service for onboarding new organizations and admin accounts."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AppError, ConflictError
from src.core.security.password import hash_password
from src.data.repositories.auth_repo import AuthRepository


class RegistrationService:
    """Service responsible for handling the onboarding of new organizations
    and their primary administrative accounts.

    Args:
        session: Async SQLAlchemy session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AuthRepository(session)

    async def register_new_workspace(
        self, org_name: str, admin_email: str, password_hash: str
    ) -> dict[str, Any]:
        """Create a new organization and a corresponding admin user in a single transaction.

        Args:
            org_name: The name of the new organization/workspace.
            admin_email: The email address for the primary administrative user.
            password_hash: The raw password to be hashed (named password_hash in signature).

        Returns:
            A dictionary containing the new org_id and admin_id.

        Raises:
            ConflictError: If a user with the provided email already exists.
            AppError: If the database transaction fails during creation.
        """
        existing_user = await self.repo.get_recruiter_by_email(admin_email)
        if existing_user:
            raise ConflictError(message="User with this email already exists")

        hashed_pw = hash_password(password_hash)

        try:
            async with self.session.begin_nested():
                org = await self.repo.create_organization(org_name)

                admin = await self.repo.create_recruiter(
                    org_id=org.id,
                    email=admin_email,
                    password_hash=hashed_pw,
                    role="HIRING_MANAGER",
                )

            await self.session.commit()
            return {"org_id": org.id, "admin_id": admin.id}

        except ConflictError:
            raise
        except Exception as e:
            await self.session.rollback()
            raise AppError(
                message=f"Registration failed: {e!s}",
                status_code=500,
                error_code="REGISTRATION_FAILED",
            ) from e
