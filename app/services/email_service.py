import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.emails import templates

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, text: str, html: str | None = None) -> None:
    """Transport layer: deliver an email via SMTP.

    Sends a multipart message: text first, HTML as the preferred alternative.
    Clients that render HTML show the pretty version; everything else
    (old clients, screen readers, our dev fallback) uses the text.

    Dev fallback: if SMTP isn't configured in .env, print the email to the
    server log instead so the flow stays testable without an email account.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP not configured — email NOT sent. To=%s Subject=%r", to, subject
        )
        logger.info("Email body (dev fallback):\n%s", text)
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    # starttls() upgrades the connection to encrypted before credentials are sent.
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    logger.info("Email sent. To=%s Subject=%r", to, subject)


def send_reset_email(to: str, reset_link: str) -> None:
    subject, text, html = templates.password_reset(
        reset_link, valid_minutes=settings.RESET_TOKEN_EXPIRE_MINUTES
    )
    send_email(to, subject, text, html)


def send_verify_email(to: str, full_name: str | None, verify_link: str) -> None:
    subject, text, html = templates.verify_email(
        full_name, verify_link, valid_minutes=settings.VERIFY_TOKEN_EXPIRE_MINUTES
    )
    send_email(to, subject, text, html)
