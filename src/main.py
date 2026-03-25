from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.error_handler import register_exception_handlers
from src.api.middleware.logging import LoggingMiddleware
from src.api.rest.app import api_router
from src.config.settings import settings
from src.observability.logging.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle events.

    Args:
        app: The FastAPI application instance.

    Yields:
        None
    """
    logger.info("application_startup", version="0.1.0")
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title="Keboli AI Interview Platform",
    description="Backend API for the Keboli AI-powered interview and evaluation platform.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)
app.add_middleware(LoggingMiddleware)

register_exception_handlers(app)

app.include_router(api_router, prefix="/api")
