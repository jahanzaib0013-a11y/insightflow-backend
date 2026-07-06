from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    # user.hashed_password is None for OAuth-only accounts — they can't password-login
    if (
        not user
        or not user.hashed_password
        or not verify_password(password, user.hashed_password)
    ):
        return None
    return user


def get_or_create_oauth_user(db: Session, email: str, full_name: str | None) -> User:
    user = get_user_by_email(db, email)
    if user:
        return user
    # is_verified=True: the OAuth provider already verified this email
    # before handing it to us.
    user = User(
        email=email, full_name=full_name, hashed_password=None, is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
