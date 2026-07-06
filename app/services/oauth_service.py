"""Talks to OAuth providers (Google, GitHub) and normalizes what they return.

Each provider exposes two functions:
  *_login_url()          — where to send the user's browser
  exchange_*_code(code)  — one-time code -> (email, full_name)

Raises OAuthError on any provider-side failure; routers translate that
into an HTTP status. Nothing in here knows about FastAPI or our database.
"""

from urllib.parse import urlencode

import httpx

from app.core.config import settings


class OAuthError(Exception):
    """A provider refused or returned something unusable."""


# ---------- Google ----------


def google_login_url() -> str:
    params = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            # Always show the account chooser instead of silently re-using
            # the browser's Google session.
            "prompt": "select_account",
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"


def exchange_google_code(code: str) -> tuple[str, str | None]:
    token_res = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    if token_res.status_code != 200:
        raise OAuthError("Failed to exchange code with Google")
    google_token = token_res.json()["access_token"]

    userinfo_res = httpx.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {google_token}"},
    )
    if userinfo_res.status_code != 200:
        raise OAuthError("Failed to fetch user info from Google")
    info = userinfo_res.json()
    return info["email"], info.get("name")


# ---------- GitHub ----------


def github_login_url() -> str:
    params = urlencode(
        {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            # user:email lets us read the email even if their profile hides it.
            "scope": "user:email",
        }
    )
    return f"https://github.com/login/oauth/authorize?{params}"


def exchange_github_code(code: str) -> tuple[str, str | None]:
    # GitHub quirk #1: without this Accept header the response is
    # form-encoded text, not JSON.
    token_res = httpx.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "code": code,
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
        },
    )
    github_token = token_res.json().get("access_token")
    if not github_token:
        raise OAuthError("Failed to exchange code with GitHub")

    auth_headers = {"Authorization": f"Bearer {github_token}"}
    profile_res = httpx.get("https://api.github.com/user", headers=auth_headers)
    if profile_res.status_code != 200:
        raise OAuthError("Failed to fetch user info from GitHub")
    profile = profile_res.json()

    # GitHub quirk #2: email is null when the user hides it on their profile;
    # then we must ask the /user/emails endpoint for the primary verified one.
    email = profile.get("email")
    if not email:
        emails_res = httpx.get(
            "https://api.github.com/user/emails", headers=auth_headers
        )
        if emails_res.status_code == 200:
            email = next(
                (
                    e["email"]
                    for e in emails_res.json()
                    if e.get("primary") and e.get("verified")
                ),
                None,
            )
    if not email:
        raise OAuthError("Could not get a verified email from GitHub")

    return email, profile.get("name")
