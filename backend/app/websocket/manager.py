"""WebSocket Connection Manager for real-time room communication."""
import asyncio
import json
import logging
import math
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Type alias: user_id -> (websocket, latitude, longitude, last_ping)
_Connection = Tuple[WebSocket, Optional[float], Optional[float], datetime]


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Connections are stored in memory as::

        {user_id: (websocket, latitude, longitude, last_ping)}

    The manager supports geo-filtered broadcasts so that only users within
    a given radius receive a given event.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, _Connection] = {}

    # ── Connection lifecycle ─────────────────────────────────────────────────

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> None:
        """Register an already-accepted WebSocket connection.

        The caller is responsible for calling ``websocket.accept()`` before
        invoking this method so that authentication can happen after the
        handshake but before any data is exchanged.
        """
        self._connections[user_id] = (websocket, latitude, longitude, datetime.utcnow())
        logger.info("WS connected: user=%s  total=%d", user_id, len(self._connections))

    def disconnect(self, user_id: str) -> None:
        """Remove a connection."""
        self._connections.pop(user_id, None)
        logger.info("WS disconnected: user=%s  total=%d", user_id, len(self._connections))

    def update_location(self, user_id: str, latitude: float, longitude: float) -> None:
        """Update the stored location for a connected user."""
        entry = self._connections.get(user_id)
        if entry:
            ws, _, _, last_ping = entry
            self._connections[user_id] = (ws, latitude, longitude, last_ping)

    def record_ping(self, user_id: str) -> None:
        """Record the timestamp of the latest ping from a user."""
        entry = self._connections.get(user_id)
        if entry:
            ws, lat, lng, _ = entry
            self._connections[user_id] = (ws, lat, lng, datetime.utcnow())

    # ── Broadcast helpers ────────────────────────────────────────────────────

    async def send_personal(self, user_id: str, event: Dict[str, Any]) -> None:
        """Send an event to a single connected user."""
        entry = self._connections.get(user_id)
        if not entry:
            return
        ws = entry[0]
        try:
            await ws.send_json(event)
        except Exception:
            self.disconnect(user_id)

    async def broadcast_to_nearby(
        self,
        event: Dict[str, Any],
        lat: float,
        lng: float,
        radius_meters: float,
    ) -> None:
        """
        Broadcast an event to all users whose last known location is within
        *radius_meters* of the given coordinates.

        Disconnected users are pruned automatically.
        """
        stale: list[str] = []
        for uid, (ws, ulat, ulng, _) in list(self._connections.items()):
            if ulat is None or ulng is None:
                continue
            if _haversine_meters(lat, lng, ulat, ulng) > radius_meters:
                continue
            try:
                await ws.send_json(event)
            except Exception:
                stale.append(uid)
        for uid in stale:
            self.disconnect(uid)

    async def broadcast_nearby_count(self, lat: float, lng: float, radius_meters: float) -> None:
        """
        Recalculate the number of connected users in the area and broadcast
        a *nearby_count_changed* event to each of them.
        """
        # Collect users within radius
        nearby_uids = [
            uid
            for uid, (_, ulat, ulng, _) in self._connections.items()
            if ulat is not None
            and ulng is not None
            and _haversine_meters(lat, lng, ulat, ulng) <= radius_meters
        ]
        count = len(nearby_uids)
        event = {"type": "nearby_count_changed", "data": {"count": count}}
        stale: list[str] = []
        for uid in nearby_uids:
            entry = self._connections.get(uid)
            if not entry:
                continue
            ws = entry[0]
            try:
                await ws.send_json(event)
            except Exception:
                stale.append(uid)
        for uid in stale:
            self.disconnect(uid)

    # ── Keep-alive ───────────────────────────────────────────────────────────

    async def ping_all(self) -> None:
        """
        Send a ping frame to every connected client.
        Stale connections (those that raise on send) are removed.
        """
        stale: list[str] = []
        for uid, (ws, lat, lng, _) in list(self._connections.items()):
            try:
                await ws.send_json({"type": "ping"})
            except Exception:
                stale.append(uid)
        for uid in stale:
            self.disconnect(uid)

    @property
    def active_count(self) -> int:
        """Return the number of currently active connections."""
        return len(self._connections)


# ── Utility ──────────────────────────────────────────────────────────────────


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two geographic points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
