"""Custom exception hierarchy for the Keboli backend.

All application-level exceptions inherit from AppError, providing
a consistent structure for error codes, HTTP status mapping, and
machine-readable error responses.
"""

from typing import Any


class AppError(Exception):
    """Base exception for all application errors.

    Args:
        message: Human-readable error description.
        status_code: HTTP status code to return to the client.
        error_code: Machine-readable error identifier (e.g. "NOT_FOUND").
        details: Optional structured data providing additional context.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist.

    Args:
        resource: The type of resource that was not found (e.g. "Assessment").
        resource_id: The identifier that was looked up.
    """

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: str | None = None,
    ) -> None:
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            message=detail,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id},
        )


class ValidationError(AppError):
    """Raised when input data fails business-rule validation.

    Args:
        message: Description of what failed validation.
        field: Optional field name that caused the error.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        field: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


class UnauthorizedError(AppError):
    """Raised when the user is not authenticated.

    Args:
        message: Description of the authentication failure.
    """

    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class ForbiddenError(AppError):
    """Raised when the user lacks permission for the requested action.

    Args:
        message: Description of what permission is missing.
    """

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
        )


class ConflictError(AppError):
    """Raised when the action conflicts with the current resource state.

    Args:
        message: Description of the conflict.
    """

    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
        )


class ExternalServiceError(AppError):
    """Raised when a call to an external service fails.

    Args:
        service_name: Name of the external service that failed.
        message: Description of the failure.
    """

    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
    ) -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name},
        )
