from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.rest.dependencies import get_db
from src.data.models.system_log import SystemLog
from src.schemas.system_log_schema import LogCreate, LogResponse
from src.observability.logging.logger import logger

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.post("/", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(log_data: LogCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_log = SystemLog(**log_data.model_dump())
        db.add(new_log)
        await db.commit()
        await db.refresh(new_log)
        return new_log
    except Exception as e:
        logger.error(f"Failed to create log entry: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create log entry")
