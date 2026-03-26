"""Tests for authentication helpers (decode_token, decode_access_token)."""
import pytest
from datetime import timedelta
from jose import jwt

import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only-32chars!")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("POSTGRES_PASSWORD", "test-password-for-unit-tests-only")
os.environ.setdefault("DEBUG", "true")

from app.services.auth import create_access_token, decode_token, decode_access_token
from app.config import settings


class TestDecodeToken:
    """decode_token returns None instead of raising on invalid input."""

    def test_valid_token_returns_payload(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_invalid_token_returns_none(self):
        assert decode_token("not-a-real-token") is None

    def test_tampered_token_returns_none(self):
        token = create_access_token({"sub": "user-123"})
        tampered = token + "x"
        assert decode_token(tampered) is None

    def test_expired_token_returns_none(self):
        token = create_access_token({"sub": "user-xyz"}, expires_delta=timedelta(seconds=-1))
        assert decode_token(token) is None

    def test_empty_string_returns_none(self):
        assert decode_token("") is None

    def test_token_contains_expected_claims(self):
        token = create_access_token({"sub": "abc", "role": "admin"})
        payload = decode_token(token)
        assert payload["sub"] == "abc"
        assert payload["role"] == "admin"
        assert "exp" in payload


class TestDecodeAccessToken:
    """decode_access_token raises HTTPException on invalid input."""

    def test_valid_token_returns_payload(self):
        token = create_access_token({"sub": "user-456"})
        payload = decode_access_token(token)
        assert payload["sub"] == "user-456"

    def test_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("bad-token")
        assert exc_info.value.status_code == 401

    def test_expired_token_raises(self):
        from fastapi import HTTPException
        token = create_access_token({"sub": "user-xyz"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        assert exc_info.value.status_code == 401


class TestCreateAccessToken:
    """create_access_token produces valid JWTs."""

    def test_token_is_string(self):
        token = create_access_token({"sub": "u1"})
        assert isinstance(token, str)

    def test_custom_expiry(self):
        token = create_access_token({"sub": "u1"}, expires_delta=timedelta(hours=1))
        payload = decode_token(token)
        assert payload is not None

    def test_sub_preserved_through_roundtrip(self):
        uid = "round-trip-user-id"
        token = create_access_token({"sub": uid})
        payload = decode_token(token)
        assert payload["sub"] == uid
