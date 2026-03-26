"""Pydantic schemas for authentication request/response serialization."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Schema for login credential submission."""

    email: EmailStr
    password: str


class RecruiterOut(BaseModel):
    """Public-facing recruiter profile data."""

    id: str
    email: EmailStr
    org_id: str


class LoginResponse(BaseModel):
    """Schema returned after successful authentication."""

    user: RecruiterOut


class OrgCreate(BaseModel):
    """Schema for registering a new organization and admin account."""

    org_name: str
    email: EmailStr
    password: str
