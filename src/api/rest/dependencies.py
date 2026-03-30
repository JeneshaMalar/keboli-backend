"""FastAPI dependency injection providers for database sessions and authentication."""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.security.jwt import decode_access_token
from src.core.security.roles import Role
from src.data.database.session import async_session_factory
from pydantic import BaseModel
import uuid

class CurrentRecruiter(BaseModel):
    """Pydantic model representing the currently authenticated user."""
    id: uuid.UUID
    email: str
    org_id: uuid.UUID
    role: str


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, closing it after the request.

    Yields:
        An AsyncSession bound to the current request lifecycle.
    """
    async with async_session_factory() as session:
        yield session


async def get_current_recruiter(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CurrentRecruiter:
    """Extract and validate the current recruiter from the JWT cookie.

    Args:
        request: The incoming HTTP request containing the auth cookie.
        db: Async database session.

    Returns:
        The authenticated CurrentRecruiter schema.

    Raises:
        HTTPException: If the cookie is missing, the token is invalid,
            or the user does not exist.
    """
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    try:
        payload = decode_access_token(token)
        recruiter_id = payload.get("sub")
        role = payload.get("role")
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from e

    if not recruiter_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    from src.data.models.recruiter import Recruiter
    recruiter = await db.get(Recruiter, recruiter_id)
    if not recruiter:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return CurrentRecruiter(
        id=recruiter.id,
        email=recruiter.email,
        org_id=recruiter.org_id,
        role=role,
    )


async def require_hiring_manager(
    recruiter: CurrentRecruiter = Depends(get_current_recruiter),
) -> CurrentRecruiter:
    """Verify the authenticated user has the HIRING_MANAGER role.

    Args:
        recruiter: The authenticated recruiter from get_current_recruiter.

    Returns:
        The recruiter if authorized.

    Raises:
        HTTPException: If the user does not have the HIRING_MANAGER role.
    """
    if recruiter.role != Role.HIRING_MANAGER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return recruiter
