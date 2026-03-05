from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.rest.app import api_router
from src.config.settings import settings
from src.observability.logging.logger import logger

app = FastAPI() 

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")