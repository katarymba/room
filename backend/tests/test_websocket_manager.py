"""Unit tests for the WebSocket ConnectionManager."""
import asyncio
import json
import math
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.websocket.manager import ConnectionManager, _haversine_meters


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_ws() -> AsyncMock:
    """Return a mock WebSocket with an async send_json method."""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


# ── _haversine_meters ─────────────────────────────────────────────────────────


class TestHaversine:
    def test_same_point_is_zero(self):
        assert _haversine_meters(55.75, 37.62, 55.75, 37.62) == 0.0

    def test_known_distance(self):
        # Moscow Kremlin to Red Square ≈ 450 m
        dist = _haversine_meters(55.7520, 37.6175, 55.7539, 37.6208)
        assert 200 < dist < 700

    def test_symmetry(self):
        d1 = _haversine_meters(55.0, 37.0, 56.0, 38.0)
        d2 = _haversine_meters(56.0, 38.0, 55.0, 37.0)
        assert abs(d1 - d2) < 1e-6


# ── ConnectionManager ─────────────────────────────────────────────────────────


class TestConnectionManager:
    def setup_method(self):
        self.manager = ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_registers_user(self):
        ws = _make_ws()
        await self.manager.connect(ws, "user1", 55.75, 37.62)
        assert self.manager.active_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes_user(self):
        ws = _make_ws()
        await self.manager.connect(ws, "user1", 55.75, 37.62)
        self.manager.disconnect("user1")
        assert self.manager.active_count == 0

    @pytest.mark.asyncio
    async def test_update_location(self):
        ws = _make_ws()
        await self.manager.connect(ws, "user1", 55.0, 37.0)
        self.manager.update_location("user1", 56.0, 38.0)
        _, lat, lng, _ = self.manager._connections["user1"]
        assert lat == 56.0
        assert lng == 38.0

    @pytest.mark.asyncio
    async def test_broadcast_to_nearby_reaches_close_user(self):
        ws = _make_ws()
        await self.manager.connect(ws, "user1", 55.75, 37.62)
        event = {"type": "message_new", "data": {"text": "hello"}}
        await self.manager.broadcast_to_nearby(event, 55.75, 37.62, radius_meters=100)
        ws.send_json.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_broadcast_to_nearby_skips_far_user(self):
        ws = _make_ws()
        # Place user ~200 km away
        await self.manager.connect(ws, "user1", 57.0, 37.62)
        event = {"type": "message_new", "data": {"text": "hello"}}
        await self.manager.broadcast_to_nearby(event, 55.75, 37.62, radius_meters=100)
        ws.send_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_broadcast_prunes_stale_connections(self):
        ws = _make_ws()
        ws.send_json.side_effect = Exception("connection closed")
        await self.manager.connect(ws, "user1", 55.75, 37.62)
        assert self.manager.active_count == 1
        event = {"type": "ping"}
        await self.manager.broadcast_to_nearby(event, 55.75, 37.62, radius_meters=100)
        assert self.manager.active_count == 0

    @pytest.mark.asyncio
    async def test_send_personal_to_missing_user_is_safe(self):
        # Should not raise even when user is not connected
        await self.manager.send_personal("nonexistent", {"type": "ping"})

    @pytest.mark.asyncio
    async def test_broadcast_nearby_count(self):
        ws = _make_ws()
        await self.manager.connect(ws, "user1", 55.75, 37.62)
        await self.manager.broadcast_nearby_count(55.75, 37.62, radius_meters=100)
        ws.send_json.assert_awaited_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "nearby_count_changed"
        assert call_args["data"]["count"] == 1

    @pytest.mark.asyncio
    async def test_ping_all(self):
        ws = _make_ws()
        await self.manager.connect(ws, "user1", 55.75, 37.62)
        await self.manager.ping_all()
        ws.send_json.assert_awaited_once_with({"type": "ping"})

    @pytest.mark.asyncio
    async def test_record_ping_updates_timestamp(self):
        ws = _make_ws()
        t_before = datetime.utcnow()
        await self.manager.connect(ws, "user1", 55.75, 37.62)
        self.manager.record_ping("user1")
        _, _, _, last_ping = self.manager._connections["user1"]
        assert last_ping >= t_before

    @pytest.mark.asyncio
    async def test_no_location_user_skipped_in_broadcast(self):
        ws = _make_ws()
        await self.manager.connect(ws, "user1")  # no lat/lng
        event = {"type": "message_new", "data": {}}
        await self.manager.broadcast_to_nearby(event, 55.75, 37.62, radius_meters=100)
        ws.send_json.assert_not_awaited()
