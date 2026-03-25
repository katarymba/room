"""Pydantic schemas for User model."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator
import re


class UserBase(BaseModel):
    """Shared user fields."""
    device_id: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user (guest or phone)."""

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is not None:
            # Basic international phone number validation
            if not re.match(r"^\+?[1-9]\d{7,14}$", v):
                raise ValueError("Invalid phone number format")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    phone: Optional[str] = None
    device_id: Optional[str] = None
    code: Optional[str] = None  # SMS verification code


class UserResponse(UserBase):
    """Schema for user response (public fields only)."""
    id: UUID
    phone_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LocationUpdate(BaseModel):
    """Schema for updating user location."""
    latitude: float
    longitude: float

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Validate latitude range."""
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Validate longitude range."""
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
