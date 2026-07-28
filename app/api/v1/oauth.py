import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.services import oauth_service, user_service
from app.services.oauth_service import OAuthError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["oauth"])


def _issue_token_redirect(
    db: Session, email: str, full_name: str | None
) -> RedirectResponse:
    """Shared final step for every provider: find-or-create the user,
    mint OUR JWT, and hand it to the frontend via the redirect URL."""
    user = user_service.get_or_create_oauth_user(db, email=email, full_name=full_name)
    token = create_access_token(user.email)
    return RedirectResponse(f"{settings.FRONTEND_URL}/login?token={token}")


@router.get("/google/login")
def google_login():
    return RedirectResponse(oauth_service.google_login_url())


@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    try:
        email, full_name = oauth_service.exchange_google_code(code)
    except OAuthError as e:
        logger.warning("Google OAuth failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    logger.info("OAuth login via Google: %s", email)
    return _issue_token_redirect(db, email, full_name)


@router.get("/github/login")
def github_login():
    return RedirectResponse(oauth_service.github_login_url())


@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    try:
        email, full_name = oauth_service.exchange_github_code(code)
    except OAuthError as e:
        logger.warning("GitHub OAuth failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    logger.info("OAuth login via GitHub: %s", email)
    return _issue_token_redirect(db, email, full_name)
