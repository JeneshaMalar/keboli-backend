from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from src.constants.enums import LogLevel

class LogCreate(BaseModel):
    level: LogLevel
    service: Optional[str] = None
    component: Optional[str] = None
    event_type: Optional[str] = None
    session_id: Optional[UUID] = None
    candidate_id: Optional[UUID] = None
    assessment_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    request_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None
    error_stack: Optional[str] = None
    duration_ms: Optional[int] = None
    status: Optional[str] = None

class LogResponse(LogCreate):
    id: UUID
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
