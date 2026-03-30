"""Authentication service for handling login and token logic."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import UnauthorizedError
from src.core.security.password import verify_password
from src.data.repositories.auth_repo import AuthRepository
from src.data.models.recruiter import Recruiter

logger = logging.getLogger(__name__)

class AuthService:
    """Service layer for authentication."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuthRepository(session)

    async def authenticate_recruiter(self, email: str, password: str) -> Recruiter:
        """Verify recruiter credentials.

        Args:
            email: Recruiter email.
            password: Provided password.

        Returns:
            The authenticated Recruiter.

        Raises:
            UnauthorizedError: If the user is not found or password does not match.
        """
        recruiter = await self.repo.get_recruiter_by_email(email)
        if not recruiter or not verify_password(password, recruiter.password_hash):
            raise UnauthorizedError(message="Invalid credentials")
        return recruiter
