"""Reaction model."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Reaction(Base):
    """Reaction (like/emoji) on a message."""

    __tablename__ = "reactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Reaction type: "like", "heart", etc.
    reaction_type = Column(String(50), default="like", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Ensure a user can only react once per message with the same reaction type
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", "reaction_type", name="uq_reaction_per_user_message"),
    )

    # Relationships
    message = relationship("Message", back_populates="reactions")
    user = relationship("User", back_populates="reactions")
