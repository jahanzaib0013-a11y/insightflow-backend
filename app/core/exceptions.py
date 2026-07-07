"""Application errors — every error the API can return, in one place.

Each error carries its HTTP status and message as class attributes.
Routers (and dependencies) just `raise EmailAlreadyRegistered()`; the
handler registered in main.py turns any AppError into the JSON response.

Adding a new error = adding a subclass here. Changing a message = one line.
"""


class AppError(Exception):
    """Base for all expected, user-facing errors."""

    status_code: int = 400
    detail: str = "Bad request"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class EmailAlreadyRegistered(AppError):
    status_code = 400
    detail = "Email already registered"


class IncorrectCredentials(AppError):
    status_code = 401
    detail = "Incorrect email or password"


class CouldNotValidateCredentials(AppError):
    status_code = 401
    detail = "Could not validate credentials"


class InvalidVerificationLink(AppError):
    status_code = 400
    detail = "Invalid or expired verification link"


class InvalidResetLink(AppError):
    status_code = 400
    detail = "Invalid or expired reset link"
