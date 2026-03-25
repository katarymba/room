"""Pydantic schemas for Reaction model."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


ALLOWED_REACTION_TYPES = {"like", "heart", "laugh", "sad", "angry"}


class ReactionCreate(BaseModel):
    """Schema for creating a reaction on a message."""
    message_id: UUID
    reaction_type: str = "like"

    @field_validator("reaction_type")
    @classmethod
    def validate_reaction_type(cls, v: str) -> str:
        """Validate reaction type is allowed."""
        if v not in ALLOWED_REACTION_TYPES:
            raise ValueError(f"Reaction type must be one of: {', '.join(ALLOWED_REACTION_TYPES)}")
        return v


class ReactionResponse(BaseModel):
    """Schema for reaction response."""
    id: UUID
    message_id: UUID
    user_id: UUID
    reaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReactionDeleteRequest(BaseModel):
    """Schema for deleting a reaction."""
    message_id: UUID
    reaction_type: str = "like"
