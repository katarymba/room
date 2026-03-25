"""Pydantic schemas for Chat and ChatMessage models."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, field_validator


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate chat message text."""
        v = v.strip()
        if not v:
            raise ValueError("Message text cannot be empty")
        if len(v) > 1000:
            raise ValueError("Message text cannot exceed 1000 characters")
        return v


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""
    id: UUID
    chat_id: UUID
    sender_id: UUID
    text: str
    created_at: datetime
    is_mine: Optional[bool] = False

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Schema for chat response."""
    id: UUID
    created_at: datetime
    other_user_id: UUID
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ChatListResponse(BaseModel):
    """Schema for list of chats."""
    chats: List[ChatResponse]
    total: int
