"""SQLAlchemy declarative base for all ORM models in the application."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    All domain models inherit from this class to share a common
    metadata registry and declarative configuration.
    """
