from fastapi import APIRouter

from src.api.rest.routes.auth import router as auth_router
from src.api.rest.routes.health import router as health_router
from src.api.rest.routes.assessment import router as assessment_router
from src.api.rest.routes.candidate import router as candidate_router
from src.api.rest.routes.invitation import router as invitation_router
from src.api.rest.routes.evaluation import router as evaluation_router
from src.api.rest.routes.livekit import router as livekit_router
from src.api.rest.websocket.interview_ws import router as websocket_router
api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(assessment_router)
api_router.include_router(candidate_router)
api_router.include_router(invitation_router)
api_router.include_router(evaluation_router)
api_router.include_router(livekit_router)
api_router.include_router(websocket_router)