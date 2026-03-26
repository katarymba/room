"""Unit tests for the WebSocket authentication helper (_authenticate)."""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.routers.websocket import _authenticate
from app.services.auth import create_access_token


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_ws(recv_text: str | None = None, recv_exception=None) -> AsyncMock:
    """Return a mock WebSocket for _authenticate tests."""
    ws = AsyncMock()
    ws.close = AsyncMock()
    if recv_exception is not None:
        ws.receive_text = AsyncMock(side_effect=recv_exception)
    elif recv_text is not None:
        ws.receive_text = AsyncMock(return_value=recv_text)
    else:
        ws.receive_text = AsyncMock(return_value="")
    return ws


def _valid_token(user_id: str = "user-123") -> str:
    return create_access_token({"sub": user_id})


def _auth_message(token: str, latitude=55.75, longitude=37.62) -> str:
    return json.dumps({"type": "auth", "token": token, "latitude": latitude, "longitude": longitude})


# ── _authenticate ─────────────────────────────────────────────────────────────


class TestAuthenticate:
    @pytest.mark.asyncio
    async def test_valid_auth_returns_user_id_and_coords(self):
        token = _valid_token("abc-123")
        ws = _make_ws(recv_text=_auth_message(token))
        user_id, lat, lng = await _authenticate(ws)
        assert user_id == "abc-123"
        assert lat == 55.75
        assert lng == 37.62
        ws.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_valid_auth_without_coords_returns_none_coords(self):
        token = _valid_token("user-xyz")
        msg = json.dumps({"type": "auth", "token": token})
        ws = _make_ws(recv_text=msg)
        user_id, lat, lng = await _authenticate(ws)
        assert user_id == "user-xyz"
        assert lat is None
        assert lng is None

    @pytest.mark.asyncio
    async def test_timeout_closes_with_1008(self):
        ws = _make_ws(recv_exception=asyncio.TimeoutError())
        user_id, lat, lng = await _authenticate(ws)
        assert user_id is None
        ws.close.assert_awaited_once_with(code=1008)

    @pytest.mark.asyncio
    async def test_malformed_json_closes_with_4001(self):
        ws = _make_ws(recv_text="not-json{{{")
        user_id, _, _ = await _authenticate(ws)
        assert user_id is None
        ws.close.assert_awaited_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_wrong_message_type_closes_with_4001(self):
        ws = _make_ws(recv_text=json.dumps({"type": "pong"}))
        user_id, _, _ = await _authenticate(ws)
        assert user_id is None
        ws.close.assert_awaited_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_missing_token_field_closes_with_4001(self):
        ws = _make_ws(recv_text=json.dumps({"type": "auth"}))
        user_id, _, _ = await _authenticate(ws)
        assert user_id is None
        ws.close.assert_awaited_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_invalid_jwt_closes_with_4001(self):
        ws = _make_ws(recv_text=json.dumps({"type": "auth", "token": "invalid.jwt.token"}))
        user_id, _, _ = await _authenticate(ws)
        assert user_id is None
        ws.close.assert_awaited_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_out_of_range_latitude_closes_with_4001(self):
        token = _valid_token()
        msg = json.dumps({"type": "auth", "token": token, "latitude": 999.0, "longitude": 37.62})
        ws = _make_ws(recv_text=msg)
        user_id, _, _ = await _authenticate(ws)
        assert user_id is None
        ws.close.assert_awaited_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_out_of_range_longitude_closes_with_4001(self):
        token = _valid_token()
        msg = json.dumps({"type": "auth", "token": token, "latitude": 55.75, "longitude": 999.0})
        ws = _make_ws(recv_text=msg)
        user_id, _, _ = await _authenticate(ws)
        assert user_id is None
        ws.close.assert_awaited_once_with(code=4001)
