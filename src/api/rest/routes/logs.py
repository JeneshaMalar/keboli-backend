from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.rest.dependencies import get_db
from src.data.models.system_log import SystemLog
from src.schemas.system_log_schema import LogCreate, LogResponse
from src.observability.logging.logger import logger

router = APIRouter(prefix="/logs", tags=["Logs"])

import uuid
from typing import Dict, Any

@router.post("/", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(log_data: LogCreate, db: AsyncSession = Depends(get_db)):
    try:
        log_dict = log_data.model_dump()
        
        # Sanitize UUID fields
        uuid_fields = ['session_id', 'candidate_id', 'assessment_id', 'user_id', 'request_id']
        
        if log_dict.get('details') is None:
            log_dict['details'] = {}
            
        for field in uuid_fields:
            val = log_dict.get(field)
            if val:
                try:
                    # Check if it's already a UUID or can be converted
                    if not isinstance(val, uuid.UUID):
                        log_dict[field] = uuid.UUID(str(val))
                except (ValueError, TypeError):
                    # Not a valid UUID, move to details and set field to None
                    log_dict['details'][f'original_{field}'] = str(val)
                    log_dict[field] = None
        
        new_log = SystemLog(**log_dict)
        db.add(new_log)
        await db.commit()
        await db.refresh(new_log)
        return new_log
    except Exception as e:
        logger.error(f"Failed to create log entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
