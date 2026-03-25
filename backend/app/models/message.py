"""Message model."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from app.database import Base


class Message(Base):
    """Message posted to a Room (anonymous, location-based)."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    # PostGIS geography point where the message was sent
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Mystery mode — author is hidden until revealed
    is_mystery = Column(Boolean, default=True, nullable=False, server_default="true")
    # List of user UUIDs that have had the author revealed to them
    revealed_to = Column(ARRAY(UUID(as_uuid=True)), default=list, nullable=False, server_default="{}")

    # Relationships
    user = relationship("User", back_populates="messages")
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete-orphan")
