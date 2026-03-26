"""User model."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from app.database import Base


class User(Base):
    """User entity. Supports both phone-based and guest (device_id) authentication."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    phone_verified = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    # PostGIS geography point (longitude, latitude) for spatial queries
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    location_updated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Subscription / freemium tier
    subscription_tier = Column(String(20), default="free", nullable=False, server_default="free")
    subscription_expires_at = Column(DateTime, nullable=True)
    daily_message_count = Column(Integer, default=0, nullable=False, server_default="0")
    last_message_reset_date = Column(Date, nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="user", cascade="all, delete-orphan")
    chats_as_user1 = relationship("Chat", foreign_keys="Chat.user1_id", back_populates="user1")
    chats_as_user2 = relationship("Chat", foreign_keys="Chat.user2_id", back_populates="user2")
