from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    DEEPGRAM_API_KEY: str
    GROQ_API_KEY: str = Field(validation_alias="groq_api_key")
    GROQ_MODEL: str
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str | None = None
 
    LIVEKIT_URL: str | None = None
    LIVEKIT_API_KEY: str | None = None
    LIVEKIT_API_SECRET: str | None = None
 
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000","http://localhost:8002","http://localhost:8001"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "allow"

settings=Settings()