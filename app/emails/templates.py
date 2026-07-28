"""One function per email the app can send.

Each returns (subject, text_body, html_body). The HTML lives in
templates/<name>.html; the plain-text version is the fallback shown by
email clients that don't render HTML (and by our dev console fallback).
"""

from app.emails.render import render


def password_reset(reset_link: str, valid_minutes: int) -> tuple[str, str, str]:
    subject = "Reset your InsightFlow password"
    text = (
        "Someone requested a password reset for your InsightFlow account.\n"
        f"Open this link to choose a new password (valid {valid_minutes} minutes):\n\n"
        f"{reset_link}\n\n"
        "If this wasn't you, you can safely ignore this email.\n"
    )
    html = render("password_reset", reset_link=reset_link, valid_minutes=valid_minutes)
    return subject, text, html


def verify_email(
    full_name: str | None, verify_link: str, valid_minutes: int
) -> tuple[str, str, str]:
    subject = "Confirm your InsightFlow email"
    name = full_name or "there"
    text = (
        f"Hi {name},\n\n"
        "Thanks for signing up for InsightFlow. Confirm your email by opening\n"
        f"this link (valid {valid_minutes} minutes):\n\n"
        f"{verify_link}\n\n"
        "If you didn't create an account, you can ignore this email.\n"
    )
    html = render(
        "verify_email", name=name, verify_link=verify_link, valid_minutes=valid_minutes
    )
    return subject, text, html
