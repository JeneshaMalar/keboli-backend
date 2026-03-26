"""Authentication routes for login, registration, and session management."""

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.config.settings import settings
from src.core.exceptions import UnauthorizedError
from src.core.security.jwt import create_access_token
from src.core.security.password import verify_password
from src.core.security.roles import Role
from src.core.services.registration_service import RegistrationService
from src.data.models.recruiter import Recruiter
from src.data.repositories.auth_repo import AuthRepository
from src.schemas.auth_schema import LoginRequest, LoginResponse, OrgCreate, RecruiterOut

router = APIRouter(prefix="/auth", tags=["auth"])


class OrgCreateResponse(BaseModel):
    """Response model for organization registration."""

    org_id: str
    admin_id: str


class LogoutResponse(BaseModel):
    """Response model for logout endpoint."""

    ok: bool


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate user",
    description="Validate credentials and set an HttpOnly JWT cookie for the session.",
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate a recruiter by email/password and issue a JWT cookie.

    Args:
        payload: Login credentials (email + password).
        response: FastAPI Response object used to set the session cookie.
        db: Async database session.

    Returns:
        LoginResponse containing the authenticated user's details.

    Raises:
        UnauthorizedError: If the credentials are invalid.
    """
    repo = AuthRepository(db)
    recruiter = await repo.get_recruiter_by_email(payload.email)
    if not recruiter or not verify_password(payload.password, recruiter.password_hash):
        raise UnauthorizedError(message="Invalid credentials")

    token = create_access_token(
        subject=str(recruiter.id), role=Role.HIRING_MANAGER.value
    )

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return LoginResponse(
        user=RecruiterOut(
            id=str(recruiter.id),
            email=recruiter.email,
            org_id=str(recruiter.org_id),
        )
    )


@router.post(
    "/register-org",
    response_model=OrgCreateResponse,
    summary="Register a new organization",
    description="Create a new organization workspace along with its first admin user.",
)
async def register_org(
    payload: OrgCreate,
    db: AsyncSession = Depends(get_db),
) -> OrgCreateResponse:
    """Register a new organization and its initial admin account.

    Args:
        payload: Organization name, admin email, and password.
        db: Async database session.

    Returns:
        OrgCreateResponse with the new org_id and admin_id.
    """
    service = RegistrationService(db)
    result = await service.register_new_workspace(
        org_name=payload.org_name,
        admin_email=payload.email,
        password_hash=payload.password,
    )
    return OrgCreateResponse(
        org_id=str(result["org_id"]), admin_id=str(result["admin_id"])
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout current user",
    description="Clear the HttpOnly session cookie to end the user's session.",
)
async def logout(response: Response) -> LogoutResponse:
    """Clear the session cookie to log the user out.

    Args:
        response: FastAPI Response object used to delete the cookie.

    Returns:
        LogoutResponse confirming the logout.
    """
    response.delete_cookie(key=settings.COOKIE_NAME, path="/")
    return LogoutResponse(ok=True)


@router.get(
    "/me",
    response_model=RecruiterOut,
    summary="Get current user",
    description="Return the profile of the currently authenticated recruiter.",
)
async def me(recruiter: Recruiter = Depends(get_current_recruiter)) -> RecruiterOut:
    """Return the authenticated recruiter's profile.

    Args:
        recruiter: The currently authenticated recruiter (injected).

    Returns:
        RecruiterOut with the user's id, email, and org_id.
    """
    return RecruiterOut(
        id=str(recruiter.id),
        email=recruiter.email,
        org_id=str(recruiter.org_id),
    )
