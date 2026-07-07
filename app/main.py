from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.db.session import Base, engine
from app.api.v1 import auth, oauth

setup_logging()

app = FastAPI()


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """One translation point: any raised AppError becomes its JSON response."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(oauth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
