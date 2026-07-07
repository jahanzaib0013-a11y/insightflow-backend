"""Shared field types — the project's vocabulary of valid values.

A rule used by more than one schema becomes a named type here, so it is
defined exactly once. `password: Password` in a schema both applies the
constraint and documents where it lives.

(FastAPI equivalent of shared/custom Joi rules in a Node validations/ folder.)
"""

from typing import Annotated

from pydantic import Field

# One password policy for the whole app: registration, reset, and any
# future "change password" endpoint import this same type.
Password = Annotated[str, Field(min_length=12)]
