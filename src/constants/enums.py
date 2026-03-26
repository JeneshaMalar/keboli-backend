"""Enumeration types shared across the Keboli domain models."""

import enum


class DifficultyLevel(str, enum.Enum):
    """Assessment difficulty levels used to calibrate interview questions."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class InvitationStatus(str, enum.Enum):
    """Lifecycle states for a candidate invitation."""

    SENT = "sent"
    CLICKED = "clicked"
    EXPIRED = "expired"
    COMPLETED = "completed"


class InterviewSessionStatus(str, enum.Enum):
    """Lifecycle states for an interview session."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class HiringRecommendation(str, enum.Enum):
    """AI or admin hiring recommendation outcomes."""

    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    REJECT = "reject"


class LogLevel(str, enum.Enum):
    """Severity levels for structured system log entries."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
