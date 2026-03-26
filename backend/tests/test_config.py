"""Tests for Settings validators (SECRET_KEY and POSTGRES_PASSWORD)."""
import os
import pytest

# Set valid env vars so the module-level `settings = Settings()` succeeds.
os.environ.setdefault("SECRET_KEY", "f47ac10b-58cc-4372-a567-0e02b2c3d479-aXk9mQ3r")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

from pydantic import ValidationError
from app.config import Settings


_VALID_KEY = "f47ac10b-58cc-4372-a567-0e02b2c3d479-aXk9mQ3r"
_VALID_PG_PASS = "Xk9mQ3rF7tY2wA5nB8cD"  # 20 chars, no weak patterns


class TestSecretKeyValidator:
    """Settings.validate_secret_key rejects weak or short keys."""

    def _make(self, key: str) -> Settings:
        return Settings(SECRET_KEY=key, DATABASE_URL="postgresql://x:x@localhost/x")

    def test_valid_key_accepted(self):
        s = self._make(_VALID_KEY)
        assert s.SECRET_KEY == _VALID_KEY

    def test_short_key_rejected(self):
        with pytest.raises(ValidationError, match="32 characters"):
            self._make("tooshort")

    def test_exactly_31_chars_rejected(self):
        with pytest.raises(ValidationError, match="32 characters"):
            self._make("a" * 31)

    def test_exactly_32_chars_accepted(self):
        s = self._make("a" * 32)
        assert len(s.SECRET_KEY) == 32

    def test_changeme_rejected(self):
        with pytest.raises(ValidationError, match="weak"):
            self._make("changeme-this-is-definitely-long-enough-but-weak")

    def test_change_me_rejected(self):
        with pytest.raises(ValidationError, match="weak"):
            self._make("change_me-this-is-definitely-long-enough-000000")

    def test_admin_rejected(self):
        with pytest.raises(ValidationError, match="weak"):
            self._make("admin-this-key-is-long-enough-but-uses-admin")

    def test_password_rejected(self):
        with pytest.raises(ValidationError, match="weak"):
            self._make("password-this-is-definitely-long-enough-nope")

    def test_secret_rejected(self):
        with pytest.raises(ValidationError, match="weak"):
            self._make("my-super-secret-key-that-is-long-enough-ok?")

    def test_1234_rejected(self):
        with pytest.raises(ValidationError, match="weak"):
            self._make("1234abcdefghijklmnopqrstuvwxyzABCDEFG")


class TestPostgresPasswordValidator:
    """Settings.validate_postgres_password rejects weak or short passwords."""

    def _make(self, pg_pass: str) -> Settings:
        return Settings(
            SECRET_KEY=_VALID_KEY,
            POSTGRES_PASSWORD=pg_pass,
            DATABASE_URL="postgresql://x:x@localhost/x",
        )

    def test_valid_password_accepted(self):
        s = self._make(_VALID_PG_PASS)
        assert s.POSTGRES_PASSWORD == _VALID_PG_PASS

    def test_none_accepted(self):
        s = Settings(SECRET_KEY=_VALID_KEY, DATABASE_URL="postgresql://x:x@localhost/x")
        assert s.POSTGRES_PASSWORD is None

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError, match="16 characters"):
            self._make("tooshort")

    def test_exactly_15_chars_rejected(self):
        with pytest.raises(ValidationError, match="16 characters"):
            self._make("a" * 15)

    def test_exactly_16_chars_accepted(self):
        s = self._make("a" * 16)
        assert s.POSTGRES_PASSWORD == "a" * 16

    def test_changeme_rejected(self):
        with pytest.raises(ValidationError, match="weak"):
            self._make("changeme-password-long-enough")

    def test_password_word_rejected(self):
        with pytest.raises(ValidationError, match="weak"):
            self._make("my-password-is-long-enough-here")

    def test_admin_rejected(self):
        with pytest.raises(ValidationError, match="weak"):
            self._make("admin-long-enough-password-here")
