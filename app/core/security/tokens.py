"""JWT creation and verification.

Three token kinds, distinguished by the `purpose` claim so they can never
be swapped: access (login sessions), password-reset links, email-verify
links. All are signed with the same SECRET_KEY from settings.
"""

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def _create_token(subject: str, minutes: int, purpose: str | None = None) -> str:
    payload: dict = {
        "sub": subject,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
    }
    if purpose:
        payload["purpose"] = purpose
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _verify_purpose_token(token: str, purpose: str) -> str | None:
    """Valid signature, unexpired, AND the right purpose — or None."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except jwt.PyJWTError:
        return None
    if payload.get("purpose") != purpose:
        return None
    return payload.get("sub")


# Purpose constants: each create/verify pair must agree on the exact string,
# so it is written once here and never inline.
PURPOSE_PASSWORD_RESET = "password-reset"
PURPOSE_EMAIL_VERIFY = "email-verify"


# --- access tokens (login sessions) ---


def create_access_token(subject: str) -> str:
    return _create_token(subject, settings.ACCESS_TOKEN_EXPIRE_MINUTES)


# --- password reset links ---


def create_reset_token(subject: str) -> str:
    return _create_token(
        subject, settings.RESET_TOKEN_EXPIRE_MINUTES, PURPOSE_PASSWORD_RESET
    )


def verify_reset_token(token: str) -> str | None:
    return _verify_purpose_token(token, PURPOSE_PASSWORD_RESET)


# --- email verification links ---


def create_verify_token(subject: str) -> str:
    return _create_token(
        subject, settings.VERIFY_TOKEN_EXPIRE_MINUTES, PURPOSE_EMAIL_VERIFY
    )


def verify_verify_token(token: str) -> str | None:
    return _verify_purpose_token(token, PURPOSE_EMAIL_VERIFY)
