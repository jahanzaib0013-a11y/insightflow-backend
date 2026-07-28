"""Importing this package registers every model with Base.metadata,
so create_all (and later, Alembic) can never silently miss a table.
Add an import line here for each new model file."""

from app.models.user import User

__all__ = ["User"]
