"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


# Patterns that indicate a placeholder or weak secret (case-insensitive check)
_WEAK_PATTERNS = ("changeme", "change_me", "change-me", "admin", "password", "secret", "1234")


def _is_weak(value: str) -> bool:
    """Return True if the value contains any known-weak pattern."""
    lower = value.lower()
    return any(pattern in lower for pattern in _WEAK_PATTERNS)


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
    SECRET_KEY: str
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

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Refuse to start when SECRET_KEY is too short or uses a weak default."""
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if _is_weak(v):
            raise ValueError(
                "SECRET_KEY must not use a weak or default value (e.g. changeme, admin, 1234). "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    @field_validator("POSTGRES_PASSWORD")
    @classmethod
    def validate_postgres_password(cls, v: Optional[str]) -> Optional[str]:
        """Refuse to start when POSTGRES_PASSWORD is set but too short or weak."""
        if v is None:
            return v
        if len(v) < 16:
            raise ValueError(
                "POSTGRES_PASSWORD must be at least 16 characters long."
            )
        if _is_weak(v):
            raise ValueError(
                "POSTGRES_PASSWORD must not use a weak or default value "
                "(e.g. changeme, admin, password)."
            )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
