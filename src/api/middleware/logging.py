"""HTTP request/response logging middleware with async database persistence."""

import asyncio
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.constants.enums import LogLevel
from src.data.database.session import async_session_factory
from src.data.models.system_log import SystemLog
from src.observability.logging.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that intercepts every request to log method, path, status, and duration.

    Logs are persisted asynchronously to the SystemLog table so that
    logging failures do not impact request processing.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Intercept incoming requests, log details, and handle exceptions gracefully.

        Args:
            request: The incoming HTTP request.
            call_next: Callable that forwards the request to the next middleware/route.

        Returns:
            The HTTP response from downstream handlers.
        """
        start_time = time.time()
        request_id = uuid.uuid4()

        ip_address: str | None = request.client.host if request.client else None
        user_agent: str | None = request.headers.get("user-agent")
        path: str = request.url.path
        method: str = request.method

        try:
            response: Response = await call_next(request)

            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            status_code = response.status_code

            level = (
                LogLevel.INFO
                if status_code < 400
                else (LogLevel.WARNING if status_code < 500 else LogLevel.ERROR)
            )
            message = f"{method} {path} - {status_code}"

            asyncio.create_task(
                self._save_log(
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
                    details={
                        "path": path,
                        "method": method,
                        "query": str(request.query_params),
                    },
                )
            )

            return response

        except Exception as e:
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)

            asyncio.create_task(
                self._save_log(
                    level=LogLevel.ERROR,
                    service="backend_main",
                    component="middleware",
                    event_type="http_request_error",
                    request_id=request_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    message=f"{method} {path} - Error: {e!s}",
                    error_stack=str(e),
                    duration_ms=duration_ms,
                    status="500",
                    details={
                        "path": path,
                        "method": method,
                        "query": str(request.query_params),
                    },
                )
            )
            raise

    @staticmethod
    async def _save_log(**kwargs: object) -> None:
        """Persist a log entry to the database asynchronously.

        Logging failures are caught and reported via structlog so they
        never impact request processing.

        Args:
            **kwargs: Key-value pairs matching the SystemLog model columns.
        """
        try:
            async with async_session_factory() as session:
                log_entry = SystemLog(**kwargs)
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            logger.error("failed_to_save_system_log", error=str(e))
