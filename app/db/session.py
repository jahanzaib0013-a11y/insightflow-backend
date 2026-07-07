from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# check_same_thread is a SQLite-only requirement (FastAPI may serve requests
# from different threads); it must not be passed to Postgres/MySQL drivers.
_connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Create any missing tables from the registered models (dev convenience;
    versioned migrations take over when there's data worth preserving).

    The models import lives inside the function to avoid a circular import —
    models import Base from this module — and to guarantee every table is
    registered before create_all runs, regardless of import order elsewhere."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
