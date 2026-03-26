"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


_DEFAULT_SECRET_KEY = "change-me-in-production-use-long-random-string"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Room API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://room_user:room_pass@localhost:5432/room_db"

    # JWT
    SECRET_KEY: str = _DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Geolocation
    DEFAULT_RADIUS_METERS: int = 100  # default search radius
    MAX_RADIUS_METERS: int = 200

    # SMS (Twilio or similar)
    SMS_PROVIDER: Optional[str] = None
    SMS_API_KEY: Optional[str] = None
    SMS_FROM_NUMBER: Optional[str] = None

    # Redis (used by rate limiter and caching in production)
    REDIS_URL: Optional[str] = None

    # Rate limits
    # Location updates: max requests per user per window
    RATE_LIMIT_LOCATION_UPDATES: int = 1        # per minute
    RATE_LIMIT_LOCATION_WINDOW_SECONDS: int = 60
    # Free-tier message cap (per day)
    FREE_DAILY_MESSAGE_LIMIT: int = 20

    # WebSocket auth timeout (seconds to wait for the auth handshake)
    WS_AUTH_TIMEOUT_SECONDS: float = 5.0

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Prevent the application from starting with the default insecure key in production."""
        # info.data may not contain DEBUG yet during validation order, so check directly
        # We raise only when the placeholder is used; callers should always override this in prod.
        if v == _DEFAULT_SECRET_KEY:
            import os
            debug = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")
            if not debug:
                raise ValueError(
                    "SECRET_KEY must be changed from the default value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
