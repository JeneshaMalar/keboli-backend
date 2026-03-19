from datetime import datetime, timedelta, timezone

from jose import jwt

from src.config.settings import settings


def create_access_token(*, subject: str, role: str, expires_minutes: int | None = None) -> str:
    """Generate a JWT access token with embedded user role and expiration."""
    expire_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode a JWT access token and return its payload, verifying signature and expiration."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
