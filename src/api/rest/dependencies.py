from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.security.jwt import decode_access_token
from src.core.security.roles import Role
from src.data.database.session import AsyncSessionLocal
from src.data.models.recruiter import Recruiter


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_recruiter(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Recruiter:
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(token)
        recruiter_id = payload.get("sub")
        role = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if not recruiter_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    recruiter = await db.get(Recruiter, recruiter_id)
    if not recruiter:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    recruiter.role = role
    return recruiter


async def require_hiring_manager(
    recruiter: Recruiter = Depends(get_current_recruiter),
) -> Recruiter:
    if recruiter.role != Role.HIRING_MANAGER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return recruiter
