from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.data.repositories.auth_repo import AuthRepository
from src.core.security.password import hash_password
class RegistrationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuthRepository(session)

    async def register_new_workspace(self, org_name: str, admin_email: str, password_hash: str):
        existing_user = await self.repo.get_recruiter_by_email(admin_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )


        hashed_pw = hash_password(password_hash)

        try:
            async with self.session.begin_nested():
                org = await self.repo.create_organization(org_name)
                
                admin = await self.repo.create_recruiter(
                    org_id=org.id,
                    email=admin_email,
                    password_hash=hashed_pw,
                    role="admin"
                )
            
            await self.session.commit()
            return {"org_id": org.id, "admin_id": admin.id}

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )