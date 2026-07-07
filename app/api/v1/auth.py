import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.services import user_service, email_service
from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyRegistered,
    IncorrectCredentials,
    InvalidResetLink,
    InvalidVerificationLink,
)
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import (
    create_access_token,
    create_reset_token,
    verify_reset_token,
    create_verify_token,
    verify_verify_token,
)
from app.api.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(
    user: UserCreate, background: BackgroundTasks, db: Session = Depends(get_db)
):
    if user_service.get_user_by_email(db, user.email):
        raise EmailAlreadyRegistered()
    new_user = user_service.create_user(db, user)
    logger.info("User registered: %s (id=%s)", new_user.email, new_user.id)
    # BackgroundTasks: the email is sent AFTER the response goes out, so
    # signup stays instant instead of waiting ~5s on the SMTP handshake.
    verify_link = f"{settings.BACKEND_URL}/auth/verify-email?token={create_verify_token(new_user.email)}"
    background.add_task(
        email_service.send_verify_email, new_user.email, new_user.full_name, verify_link
    )
    return {"id": new_user.id, "email": new_user.email}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Target of the link in the verification email. Browser GET → flip the
    flag → land the user on the login page with a success marker."""
    email = verify_verify_token(token)
    if not email:
        raise InvalidVerificationLink()
    user = user_service.get_user_by_email(db, email)
    if not user:
        raise InvalidVerificationLink()
    if not user.is_verified:
        user.is_verified = True
        db.commit()
        logger.info("Email verified: %s", user.email)
    return RedirectResponse(f"{settings.FRONTEND_URL}/login?verified=1")


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = user_service.authenticate(db, form_data.username, form_data.password)
    if not user:
        # WARNING level: repeated failures for one account are the signature
        # of a guessing attack — worth being able to filter for.
        logger.warning("Failed login attempt for %s", form_data.username)
        raise IncorrectCredentials()
    logger.info("Login: %s", user.email)
    return {"access_token": create_access_token(user.email), "token_type": "bearer"}


@router.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
    }


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = user_service.get_user_by_email(db, body.email)
    # Soft-verification policy: password reset requires a verified email —
    # otherwise anyone who typo-registered someone else's address could
    # receive that person's reset links.
    if user and user.is_verified:
        token = create_reset_token(user.email)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        email_service.send_reset_email(to=user.email, reset_link=reset_link)
    # Same response whether the email exists or not, so attackers can't
    # use this endpoint to discover which emails are registered.
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = verify_reset_token(body.token)
    if not email:
        raise InvalidResetLink()
    user = user_service.get_user_by_email(db, email)
    if not user:
        raise InvalidResetLink()
    user_service.set_password(db, user, body.new_password)
    logger.info("Password reset completed: %s", user.email)
    return {"message": "Password updated. You can now sign in."}
