"""Pydantic schemas for WebSocket message validation."""
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class WsAuthMessage(BaseModel):
    """First message sent by the client to authenticate the WebSocket connection."""

    type: Literal["auth"]
    token: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("token must not be empty")
        return v.strip()

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not -90 <= v <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not -180 <= v <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return v


class WsLocationUpdateMessage(BaseModel):
    """Client → Server: update the user's current location."""

    type: Literal["location_update"]
    latitude: float
    longitude: float

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return v


class WsPongMessage(BaseModel):
    """Client → Server: heartbeat reply."""

    type: Literal["pong"]
