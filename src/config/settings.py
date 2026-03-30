"""Application configuration loaded from environment variables via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Keboli backend.

    All values are loaded from environment variables (or a .env file)
    with sensible defaults for local development where appropriate.

    Attributes:
        DATABASE_URL: Async PostgreSQL connection string.
        SECRET_KEY: Secret key for JWT signing.
        ALGORITHM: JWT signing algorithm.
        ACCESS_TOKEN_EXPIRE_MINUTES: Token TTL in minutes.
        DEEPGRAM_API_KEY: API key for Deepgram STT/TTS services.
        LIVEKIT_URL: WebSocket URL for the LiveKit server.
        LIVEKIT_API_KEY: API key for LiveKit token generation.
        LIVEKIT_API_SECRET: API secret for LiveKit token signing.
        SENDGRID_API_KEY: API key for SendGrid email delivery.
        SENDGRID_FROM_EMAIL: Sender email address for outbound emails.
        FRONTEND_URL: Public URL of the frontend application.
        FRONTEND_ORIGIN: Allowed CORS origin for the frontend.
        INTERVIEW_AGENT_URL: Internal URL of the AI interview agent service.
        EVALUATION_SERVICE_URL: Internal URL of the evaluation service.
        CORS_ORIGINS: List of allowed CORS origins.
        COOKIE_NAME: Name of the authentication cookie.
        COOKIE_SECURE: Whether the cookie requires HTTPS.
        COOKIE_SAMESITE: SameSite policy for the auth cookie.
        COOKIE_DOMAIN: Domain scope for the auth cookie.
    """

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/keboli"
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DEEPGRAM_API_KEY: str = ""

    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = ""

    FRONTEND_URL: str
    FRONTEND_ORIGIN: str
    INTERVIEW_AGENT_URL: str
    EVALUATION_SERVICE_URL: str

    CORS_ORIGINS: list[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
