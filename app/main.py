from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import v1
from app.api.errors import app_error_handler
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.models import init_db

setup_logging()


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)

    init_db()

    app.include_router(v1.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
