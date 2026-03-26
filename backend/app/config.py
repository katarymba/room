"""Application configuration using pydantic-settings."""
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


_DEFAULT_SECRET_KEY = "change-me-in-production-use-long-random-string"

# Passwords/keys that are considered trivially weak
_WEAK_VALUES = frozenset({"admin", "1234", "12345678", "changeme", "password", "secret", "test"})


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Room API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://room_user:room_pass@localhost:5432/room_db"
    POSTGRES_PASSWORD: Optional[str] = None

    # JWT
    SECRET_KEY: str = _DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes for access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30    # 30 days for refresh tokens

    # Redis
    REDIS_URL: Optional[str] = None

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
        """Prevent the application from starting with a weak or default SECRET_KEY."""
        debug = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")
        if debug:
            return v
        if v == _DEFAULT_SECRET_KEY or v.startswith("CHANGE_ME") or v.lower() in _WEAK_VALUES:
            raise ValueError(
                "SECRET_KEY must be changed from the default value in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    @field_validator("POSTGRES_PASSWORD")
    @classmethod
    def validate_postgres_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate that POSTGRES_PASSWORD is strong enough when provided."""
        if v is None:
            return v
        debug = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")
        if debug:
            return v
        if v.lower() in _WEAK_VALUES:
            raise ValueError(
                "POSTGRES_PASSWORD is too weak. Use a strong password with at least 16 characters."
            )
        if len(v) < 16:
            raise ValueError(
                "POSTGRES_PASSWORD must be at least 16 characters long."
            )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
