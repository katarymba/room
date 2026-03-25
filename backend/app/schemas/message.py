"""Pydantic schemas for Message model."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class MessageCreate(BaseModel):
    """Schema for creating a new room message."""
    text: str
    latitude: float
    longitude: float

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate message text length."""
        v = v.strip()
        if not v:
            raise ValueError("Message text cannot be empty")
        if len(v) > 500:
            raise ValueError("Message text cannot exceed 500 characters")
        return v

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: UUID
    text: str
    created_at: datetime
    reaction_count: Optional[int] = 0
    user_has_reacted: Optional[bool] = False
    # Mystery mode fields
    is_mystery: bool = True
    author_revealed: bool = False
    author_username: Optional[str] = None

    class Config:
        from_attributes = True


class NearbyMessagesRequest(BaseModel):
    """Schema for requesting nearby messages."""
    latitude: float
    longitude: float
    radius_meters: Optional[int] = 100

    @field_validator("radius_meters")
    @classmethod
    def validate_radius(cls, v: int) -> int:
        if v < 10 or v > 200:
            raise ValueError("Radius must be between 10 and 200 meters")
        return v
