"""Every model is imported here, registering it with Base.metadata —
so init_db can never silently miss a table. One import per model file."""

from app.db.session import Base, engine
from app.models.user import User

__all__ = ["User", "init_db"]


def init_db() -> None:
    """Create any missing tables (dev convenience; migrations come later)."""
    Base.metadata.create_all(bind=engine)
