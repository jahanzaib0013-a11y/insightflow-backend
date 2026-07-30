"""HTTP error handlers — where raised AppErrors become JSON responses.

Lives in api/ (the HTTP layer) because translating exceptions to responses
is HTTP work; the exception classes themselves stay framework-free in
core/exceptions.py. Registered in main.py via app.add_exception_handler.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
