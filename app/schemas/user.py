"""Shapes describing users themselves."""

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.fields import Password


class UserCreate(BaseModel):
    full_name: str | None = None
    email: EmailStr
    password: Password


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    is_verified: bool

    model_config = ConfigDict(
        from_attributes=True
    )  # lets Pydantic read from ORM objects
