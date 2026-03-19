from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api.rest.dependencies import get_db
import time

router = APIRouter()

@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    start = time.time()

    health_status = {
        "status": "ok",
        "services": {
            "database": "unknown"
        }
    }

    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["database"] = "disconnected"
        health_status["error"] = str(e)

    health_status["response_time_ms"] = round((time.time() - start) * 1000, 2)

    return health_status