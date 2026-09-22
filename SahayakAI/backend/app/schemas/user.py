"""
User Pydantic Schemas.
Defines validation and serialization models for user accounts.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from backend.app.schemas.common import TimestampSchema


class UserBase(BaseModel):
    """Base user fields."""

    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    email: EmailStr = Field(..., description="Unique email address")


class UserCreate(UserBase):
    """Payload required to create a new user."""

    pass


class UserUpdate(BaseModel):
    """Payload for updating user details."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None


class UserRead(UserBase, TimestampSchema):
    """Public user response schema."""

    id: int

    model_config = ConfigDict(from_attributes=True)
