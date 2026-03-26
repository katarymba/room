"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional

_DEFAULT_SECRET_KEY = "change-me-in-production-use-long-random-string"

_WEAK_PASSWORDS = {"admin", "1234", "changeme", "password", "secret", "12345678", "room"}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Room API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://room_user:room_pass@localhost:5432/room_db"
    POSTGRES_PASSWORD: str = "changeme"

    # Redis
    REDIS_URL: str = ""

    # JWT
    SECRET_KEY: str = _DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30    # 30 days

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Geolocation
    DEFAULT_RADIUS_METERS: int = 100  # default search radius
    MAX_RADIUS_METERS: int = 200

    # SMS (Twilio or similar)
    SMS_PROVIDER: Optional[str] = None
    SMS_API_KEY: Optional[str] = None
    SMS_FROM_NUMBER: Optional[str] = None

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Prevent the application from starting with a weak or default key in production."""
        import os
        debug = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")
        if not debug:
            if v == _DEFAULT_SECRET_KEY or len(v) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters and not the default value. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
        return v

    @field_validator("POSTGRES_PASSWORD")
    @classmethod
    def validate_postgres_password(cls, v: str) -> str:
        """Prevent weak database passwords in production."""
        import os
        debug = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")
        if not debug:
            if v.lower() in _WEAK_PASSWORDS or len(v) < 16:
                raise ValueError(
                    "POSTGRES_PASSWORD is too weak. Use at least 16 characters and avoid "
                    "common passwords like 'changeme', 'admin', or 'password'."
                )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
