from sqlalchemy import Boolean, Column, Integer, String
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(
        String, nullable=True
    )  # null for OAuth-only users (Google/GitHub)
    # False until the user clicks the link in the verification email.
    # OAuth users start True — Google/GitHub already verified the address.
    is_verified = Column(Boolean, default=False, nullable=False)
