"""Role definitions for authorization within the Keboli platform."""

from enum import Enum


class Role(str, Enum):
    """Enumeration of application-level authorization roles."""

    HIRING_MANAGER = "HIRING_MANAGER"
