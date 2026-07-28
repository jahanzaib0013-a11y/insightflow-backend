"""Central logging setup — called once at startup (main.py).

Modules keep using the stdlib interface:
    logger = logging.getLogger(__name__)
Loguru is installed UNDERNEATH as the renderer: an InterceptHandler routes
every stdlib record (ours, uvicorn's, any library's) into loguru, which
formats it — colors, aligned columns, readable tracebacks.

This keeps the codebase decoupled from the tool: removing loguru would mean
reverting only this file.
"""

import logging
import sys

from loguru import logger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    """Forwards stdlib logging records into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Map the stdlib level name to loguru's, if it exists there.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # Carry the stdlib logger's name (e.g. app.api.v1.auth) into loguru
        # explicitly — frame-guessing is unreliable.
        logger.bind(logger_name=record.name).opt(exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    # Route ALL stdlib logging (root logger) through the interceptor.
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    # Also capture uvicorn's own loggers, which install their own handlers.
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).handlers = [InterceptHandler()]

    # Loguru output: one sink, to stderr, honoring LOG_LEVEL from .env.
    logger.remove()
    logger.configure(extra={"logger_name": "app"})  # default for direct loguru calls
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[logger_name]}</cyan> - <level>{message}</level>"
        ),
    )
