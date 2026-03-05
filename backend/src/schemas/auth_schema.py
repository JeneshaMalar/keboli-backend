from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RecruiterOut(BaseModel):
    id: str
    email: EmailStr
    org_id: str


class LoginResponse(BaseModel):
    user: RecruiterOut

class OrgCreate(BaseModel):
    org_name: str
    email: EmailStr
    password: str