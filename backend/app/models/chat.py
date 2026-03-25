"""Chat and ChatMessage models."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Chat(Base):
    """Private 1-on-1 chat between two users. Created when both users mutually like each other."""

    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user1_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Each pair of users can only have one chat
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_chat_users"),
    )

    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="chats_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="chats_as_user2")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")


class ChatMessage(Base):
    """A message within a private chat."""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User")
