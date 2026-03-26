"""WebSocket router — real-time room events.

Authentication flow (message-based, not query-param):
  1. Client connects to ``/ws/room`` (no token in the URL).
  2. Server sends ``{"type": "auth_required"}``.
  3. Client replies with ``{"type": "auth", "token": "<jwt>"}``.
  4. Server validates the token and sends ``{"type": "auth_success"}``
     or closes with code 4001.
"""
import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import decode_token
from app.services.rate_limiter import check_rate_limit
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()

# The global manager is injected from main.py via app.state
_PING_INTERVAL = 30  # seconds
_AUTH_TIMEOUT = 5    # seconds to wait for the auth message


async def _get_manager(websocket: WebSocket) -> ConnectionManager:
    return websocket.app.state.ws_manager


@router.websocket("/room")
async def websocket_room(
    websocket: WebSocket,
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time room events.

    Authentication: after connecting the client must send an auth message
    within 10 seconds::

        {"type": "auth", "token": "<jwt>"}

    The server replies with::

        {"type": "auth_success"}

    or closes with code 4001 on failure.

    **Client → Server messages:**
    ```json
    {"type": "location_update", "latitude": 55.7, "longitude": 37.6}
    {"type": "pong"}
    ```

    **Server → Client events:**
    ```json
    {"type": "auth_required"}
    {"type": "auth_success"}
    {"type": "message_new",          "data": { ...MessageResponse }}
    {"type": "reaction_added",       "data": {"message_id": "...", "new_count": 5}}
    {"type": "nearby_count_changed", "data": {"count": 3}}
    {"type": "ping"}
    ```
    """
    # ── Accept the TCP connection first ──────────────────────────────────────
    await websocket.accept()

    # ── Rate-limit connections per IP (best-effort; IP may not be available) ─
    client_ip: str = ""
    if websocket.client:
        client_ip = websocket.client.host or ""

    # ── Authenticate via message handshake ───────────────────────────────────
    await websocket.send_json({"type": "auth_required"})
    user_id: Optional[str] = None

    try:
        raw_auth = await asyncio.wait_for(websocket.receive_text(), timeout=_AUTH_TIMEOUT)
        auth_msg = json.loads(raw_auth)
        if auth_msg.get("type") == "auth":
            token = auth_msg.get("token", "")
            payload = decode_token(token)
            if payload:
                user_id = payload.get("sub")
    except (asyncio.TimeoutError, json.JSONDecodeError, Exception):
        pass

    if not user_id:
        await websocket.close(code=4001)
        return

    # ── Connection rate limit ─────────────────────────────────────────────────
    # Use IP as the identifier when rate-limiting connections
    conn_key = client_ip or user_id
    # Retrieve user tier for rate limiting (default to "free" if DB unavailable)
    user_tier = "free"
    try:
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user_tier = user.tier or "free"
    except Exception:
        pass

    conn_allowed, _ = check_rate_limit(conn_key, user_tier, "connections_per_hour")
    if not conn_allowed:
        await websocket.send_json({
            "type": "error",
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many connections. Please try again later.",
        })
        await websocket.close(code=4029)
        return

    await websocket.send_json({"type": "auth_success"})

    manager: ConnectionManager = websocket.app.state.ws_manager

    # ── Connect ───────────────────────────────────────────────────────────────
    await manager.connect(websocket, user_id, latitude, longitude)

    # Notify connected peers about updated nearby count
    if latitude is not None and longitude is not None:
        asyncio.create_task(
            manager.broadcast_nearby_count(latitude, longitude, radius_meters=100)
        )

    # ── Ping loop ─────────────────────────────────────────────────────────────
    async def _ping_loop() -> None:
        while True:
            await asyncio.sleep(_PING_INTERVAL)
            try:
                await websocket.send_json({"type": "ping"})
                manager.record_ping(user_id)
            except Exception:
                break

    ping_task = asyncio.create_task(_ping_loop())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "location_update":
                lat = msg.get("latitude")
                lng = msg.get("longitude")
                if lat is not None and lng is not None:
                    # Validate coordinate ranges
                    try:
                        lat_f, lng_f = float(lat), float(lng)
                        if -90 <= lat_f <= 90 and -180 <= lng_f <= 180:
                            manager.update_location(user_id, lat_f, lng_f)
                            asyncio.create_task(
                                manager.broadcast_nearby_count(lat_f, lng_f, radius_meters=100)
                            )
                    except (ValueError, TypeError):
                        pass

            elif msg_type == "pong":
                manager.record_ping(user_id)

    except WebSocketDisconnect:
        pass
    finally:
        ping_task.cancel()
        manager.disconnect(user_id)
        # Broadcast updated count after disconnect
        entry_lat = latitude
        entry_lng = longitude
        if entry_lat is not None and entry_lng is not None:
            asyncio.create_task(
                manager.broadcast_nearby_count(entry_lat, entry_lng, radius_meters=100)
            )
