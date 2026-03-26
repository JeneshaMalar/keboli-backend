"""JWT token creation and verification using python-jose."""

from datetime import datetime, timedelta, timezone

from jose import jwt

from src.config.settings import settings


def create_access_token(
    *, subject: str, role: str, expires_minutes: int | None = None
) -> str:
    """Generate a signed JWT access token with embedded user role and expiration.

    Args:
        subject: The user identifier (recruiter UUID) stored as the 'sub' claim.
        role: Authorization role stored in the token payload.
        expires_minutes: Custom expiration in minutes; falls back to settings.

    Returns:
        An encoded JWT string.
    """
    expire_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, object]:
    """Decode and verify a JWT access token.

    Args:
        token: The encoded JWT string.

    Returns:
        The decoded token payload as a dictionary.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
