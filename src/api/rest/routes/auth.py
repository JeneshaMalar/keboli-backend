from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_current_recruiter, get_db
from src.config.settings import settings
from src.core.security.jwt import create_access_token
from src.core.security.password import verify_password
from src.core.security.roles import Role
from src.data.models.recruiter import Recruiter
from src.schemas.auth_schema import LoginRequest, LoginResponse, RecruiterOut, OrgCreate
from src.core.services.registration_service import RegistrationService


router = APIRouter(prefix="/auth", tags=["auth"])



@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Recruiter).where(Recruiter.email == payload.email))
    recruiter = result.scalar_one_or_none()
    if not recruiter or not verify_password(payload.password, recruiter.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(recruiter.id), role=Role.HIRING_MANAGER.value)

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

    return LoginResponse(user=RecruiterOut(id=str(recruiter.id), email=recruiter.email, org_id=str(recruiter.org_id)))

@router.post("/register-org")
async def register_org(payload: OrgCreate, db: AsyncSession = Depends(get_db)):
    service = RegistrationService(db)
    return await service.register_new_workspace(
        org_name=payload.org_name,
        admin_email=payload.email,
        password_hash=payload.password 
    )

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key=settings.COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=RecruiterOut)
async def me(recruiter: Recruiter = Depends(get_current_recruiter)):
    return RecruiterOut(id=str(recruiter.id), email=recruiter.email, org_id=str(recruiter.org_id))
