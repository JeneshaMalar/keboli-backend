import asyncio
import time
import uuid

from fastapi import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from src.constants.enums import LogLevel
from src.data.database.session import async_session_factory
from src.data.models.system_log import SystemLog
from src.observability.logging.logger import logger


class LoggingMiddleware:
    """ASGI middleware that logs HTTP requests and responses.

    Logs are persisted asynchronously to the SystemLog table.
    This pure ASGI implementation avoids the ContextVar issues
    associated with Starlette's BaseHTTPMiddleware.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process an ASGI request-response cycle.

        Args:
            scope: The ASGI scope (connection metadata).
            receive: Callable to receive messages from the client.
            send: Callable to send messages to the client.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        request_id = uuid.uuid4()
        request = Request(scope)

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        path = request.url.path
        method = request.method

        status_code = [500]  # Default until we see the start message

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
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
        else:
            duration_ms = int((time.time() - start_time) * 1000)
            final_status = status_code[0]
            level = (
                LogLevel.INFO
                if final_status < 400
                else (LogLevel.WARNING if final_status < 500 else LogLevel.ERROR)
            )

            asyncio.create_task(
                self._save_log(
                    level=level,
                    service="backend_main",
                    component="middleware",
                    event_type="http_request",
                    request_id=request_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    message=f"{method} {path} - {final_status}",
                    duration_ms=duration_ms,
                    status=str(final_status),
                    details={
                        "path": path,
                        "method": method,
                        "query": str(request.query_params),
                    },
                )
            )

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
