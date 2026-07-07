from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import app_error_handler
from app.api.v1 import auth, oauth
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.db.session import Base, engine

setup_logging()


def create_app() -> FastAPI:
    """App factory: builds and wires a FastAPI instance.

    Lets tests or scripts construct fresh, differently-configured apps
    instead of sharing one module-level global."""
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)

    Base.metadata.create_all(bind=engine)

    app.include_router(auth.router)
    app.include_router(oauth.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
