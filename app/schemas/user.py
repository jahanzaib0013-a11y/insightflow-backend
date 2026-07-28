"""Shapes describing users themselves."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str | None = None
    email: EmailStr
    password: str = Field(min_length=12)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    is_verified: bool

    model_config = ConfigDict(
        from_attributes=True
    )  # lets Pydantic read from ORM objects
