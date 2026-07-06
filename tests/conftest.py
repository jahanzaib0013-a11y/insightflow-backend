"""Shared test fixtures.

Two kinds of isolation, so tests can never touch anything real:
- Database: each test gets a fresh in-memory SQLite, swapped in through
  FastAPI's dependency_overrides — the real insightflow.db is never opened.
- Email: the SMTP sender is replaced with a recorder, so no test ever
  sends real mail; tests can also assert on what WOULD have been sent.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.services import email_service


@pytest.fixture()
def db_session():
    # StaticPool keeps the single in-memory DB alive across connections
    # within one test; a new engine per test = a clean, empty DB per test.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    # dependency_overrides: every endpoint that asks for Depends(get_db)
    # receives the test session instead of the real one.
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def outbox(monkeypatch):
    """Replaces real SMTP with an in-memory outbox, for every test (autouse).
    Tests read `outbox` to assert on sent email."""
    sent = []

    def fake_send_email(to, subject, text, html=None):
        sent.append({"to": to, "subject": subject, "text": text, "html": html})

    monkeypatch.setattr(email_service, "send_email", fake_send_email)
    return sent
