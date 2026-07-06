"""End-to-end tests for the auth API — every behavior the system guarantees."""

from app.core.security import (
    create_access_token,
    create_reset_token,
    create_verify_token,
)
from app.services import user_service

EMAIL = "user@example.com"
PASSWORD = "longenoughpassword"


def register(client, email=EMAIL, password=PASSWORD, full_name="Test User"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )


def login(client, email=EMAIL, password=PASSWORD):
    return client.post("/auth/login", data={"username": email, "password": password})


def verify(client, db, email=EMAIL):
    """Mark a user verified via the real endpoint."""
    token = create_verify_token(email)
    return client.get(f"/auth/verify-email?token={token}", follow_redirects=False)


# ---------- register ----------


def test_register_returns_user(client):
    res = register(client)
    assert res.status_code == 200
    assert res.json()["email"] == EMAIL


def test_register_sends_verification_email(client, outbox):
    register(client)
    assert len(outbox) == 1
    assert outbox[0]["to"] == EMAIL
    assert "verify-email?token=" in outbox[0]["text"]


def test_register_duplicate_email_is_400(client):
    register(client)
    res = register(client)
    assert res.status_code == 400
    assert res.json()["detail"] == "Email already registered"


def test_register_short_password_is_422(client):
    res = register(client, password="short")
    assert res.status_code == 422


def test_register_invalid_email_is_422(client):
    res = register(client, email="notanemail")
    assert res.status_code == 422


def test_password_is_stored_hashed(client, db_session):
    register(client)
    user = user_service.get_user_by_email(db_session, EMAIL)
    assert user.hashed_password != PASSWORD
    assert user.hashed_password.startswith("$2b$")


# ---------- login ----------


def test_login_returns_token(client):
    register(client)
    res = login(client)
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_is_401(client):
    register(client)
    res = login(client, password="wrongpassword!")
    assert res.status_code == 401


def test_login_unknown_email_is_401(client):
    res = login(client)
    assert res.status_code == 401


def test_oauth_only_user_cannot_password_login(client, db_session):
    user_service.get_or_create_oauth_user(
        db_session, email=EMAIL, full_name="OAuth User"
    )
    res = login(client, password="anythingatall!")
    assert res.status_code == 401


# ---------- protected endpoint ----------


def test_me_without_token_is_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_garbage_token_is_401(client):
    res = client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert res.status_code == 401


def test_me_returns_current_user(client):
    register(client)
    token = login(client).json()["access_token"]
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == EMAIL


# ---------- email verification ----------


def test_new_user_starts_unverified(client, db_session):
    register(client)
    assert user_service.get_user_by_email(db_session, EMAIL).is_verified is False


def test_verify_email_flips_flag_and_redirects(client, db_session):
    register(client)
    res = verify(client, db_session)
    assert res.status_code == 307
    assert "verified=1" in res.headers["location"]
    assert user_service.get_user_by_email(db_session, EMAIL).is_verified is True


def test_login_token_rejected_as_verify_link(client, db_session):
    register(client)
    res = client.get(
        f"/auth/verify-email?token={create_access_token(EMAIL)}",
        follow_redirects=False,
    )
    assert res.status_code == 400
    assert user_service.get_user_by_email(db_session, EMAIL).is_verified is False


def test_oauth_users_start_verified(db_session):
    user = user_service.get_or_create_oauth_user(
        db_session, email=EMAIL, full_name=None
    )
    assert user.is_verified is True


# ---------- password reset ----------


def test_forgot_password_response_hides_whether_email_exists(client):
    res_known = client.post("/auth/forgot-password", json={"email": EMAIL})
    res_unknown = client.post(
        "/auth/forgot-password", json={"email": "nobody@example.com"}
    )
    assert res_known.status_code == res_unknown.status_code == 200
    assert res_known.json() == res_unknown.json()


def test_forgot_password_unverified_user_gets_no_email(client, outbox):
    register(client)
    outbox.clear()  # drop the verification email
    client.post("/auth/forgot-password", json={"email": EMAIL})
    assert outbox == []


def test_forgot_password_verified_user_gets_reset_email(client, db_session, outbox):
    register(client)
    verify(client, db_session)
    outbox.clear()
    client.post("/auth/forgot-password", json={"email": EMAIL})
    assert len(outbox) == 1
    assert "reset-password?token=" in outbox[0]["text"]


def test_reset_password_full_flow(client, db_session):
    register(client)
    token = create_reset_token(EMAIL)
    res = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "mynewlongpassword"},
    )
    assert res.status_code == 200
    assert login(client, password="mynewlongpassword").status_code == 200
    assert login(client, password=PASSWORD).status_code == 401  # old one dead


def test_reset_password_rejects_login_token(client):
    register(client)
    res = client.post(
        "/auth/reset-password",
        json={"token": create_access_token(EMAIL), "new_password": "mynewlongpassword"},
    )
    assert res.status_code == 400


def test_reset_password_short_new_password_is_422(client):
    register(client)
    res = client.post(
        "/auth/reset-password",
        json={"token": create_reset_token(EMAIL), "new_password": "short"},
    )
    assert res.status_code == 422
