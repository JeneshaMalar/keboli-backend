import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from src.data.database.session import AsyncSessionLocal
from src.data.models.system_log import SystemLog
from src.constants.enums import LogLevel
from src.observability.logging.logger import logger
import asyncio

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = uuid.uuid4()
        
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        path = request.url.path
        method = request.method
        
        try:
            response = await call_next(request)
            
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            status_code = response.status_code
            
            level = LogLevel.INFO if status_code < 400 else (LogLevel.WARNING if status_code < 500 else LogLevel.ERROR)
            message = f"{method} {path} - {status_code}"
            
            asyncio.create_task(
                self.save_log(
                    level=level,
                    service="backend_main",
                    component="middleware",
                    event_type="http_request",
                    request_id=request_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    message=message,
                    duration_ms=duration_ms,
                    status=str(status_code),
                    details={"path": path, "method": method, "query": str(request.query_params)}
                )
            )
            
            return response
            
        except Exception as e:
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            asyncio.create_task(
                self.save_log(
                    level=LogLevel.ERROR,
                    service="backend_main",
                    component="middleware",
                    event_type="http_request_error",
                    request_id=request_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    message=f"{method} {path} - Error: {str(e)}",
                    error_stack=str(e),
                    duration_ms=duration_ms,
                    status="500",
                    details={"path": path, "method": method, "query": str(request.query_params)}
                )
            )
            raise e
            
    async def save_log(self, **kwargs):
        try:
            async with AsyncSessionLocal() as session:
                log_entry = SystemLog(**kwargs)
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to save system log in middleware: {str(e)}")
