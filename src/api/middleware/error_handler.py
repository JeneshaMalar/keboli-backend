from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.exceptions import AppError
from src.observability.logging.logger import logger


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application.

    Args:
        app: The FastAPI application instance to register handlers on.
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Convert AppError exceptions into structured JSON error responses.

        Args:
            request: The incoming HTTP request that triggered the error.
            exc: The AppError instance containing error details.

        Returns:
            A JSONResponse with the appropriate status code and error body.
        """
        logger.error(
            "app_error",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            path=str(request.url.path),
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
