"""Database plumbing: the engine, the session factory, and the Base registry.

Everything here answers one of four questions:
  1. Where is the data?          -> engine
  2. How do I talk to it?        -> SessionLocal / get_db
  3. How are tables described?   -> Base (models inherit from it)
  4. How do tables get created?  -> init_db
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# --- engine: the app's single connection (pool) to the database ---------

# check_same_thread is a SQLite-only requirement (FastAPI may serve requests
# from different threads); it must not be passed to Postgres/MySQL drivers.
_connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)

# --- sessions: one short-lived transaction workspace per request --------

SessionLocal = sessionmaker(bind=engine)

# --- models: every table class inherits from Base to register itself ----

Base = declarative_base()


def init_db() -> None:
    """Create any missing tables from the registered models.

    Dev convenience — versioned migrations (Alembic) take over the day
    there is data worth preserving. The models import lives inside the
    function to avoid a circular import (models import Base from here)
    and to guarantee registration regardless of import order elsewhere.
    """
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: lend a session for one request, always close it.

    Endpoints receive it via `db: Session = Depends(get_db)` — setup runs
    to the yield, the endpoint uses the session, teardown runs after the
    response, even if the endpoint raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
