from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, loaded from the .env file / environment variables.

    Values here are defaults; anything in .env overrides them. This is where
    secrets belong — never hardcoded in source files.
    """

    FRONTEND_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"

    # Auth / JWT
    SECRET_KEY: str = "dev-secret-change-me"  # real value comes from .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RESET_TOKEN_EXPIRE_MINUTES: int = 15
    VERIFY_TOKEN_EXPIRE_MINUTES: int = 60

    # OAuth providers (values come from .env)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/auth/google/callback"
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://127.0.0.1:8000/auth/github/callback"

    # Email (Gmail SMTP). Leave SMTP_USER empty to fall back to printing
    # reset links in the server log instead of sending real mail.
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""  # a Gmail App Password, not your real password

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
