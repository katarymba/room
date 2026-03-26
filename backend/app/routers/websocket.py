"""WebSocket router — real-time room events."""
import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.config import settings
from app.rate_limiter import rate_limiter
from app.schemas.websocket import WsAuthMessage, WsLocationUpdateMessage
from app.services.auth import decode_token
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()

# The global manager lives on app.state (set in main.py)
_PING_INTERVAL = 30  # seconds


@router.websocket("/room")
async def websocket_room(websocket: WebSocket):
    """
    WebSocket endpoint for real-time room events.

    **Authentication handshake**

    After the TCP connection is established the client **must** send an auth
    message as its very first frame (within ``WS_AUTH_TIMEOUT_SECONDS``):

    ```json
    {
      "type": "auth",
      "token": "<jwt>",
      "latitude": 55.7,
      "longitude": 37.6
    }
    ```

    If the message is missing, malformed, or the token is invalid the server
    closes the connection with code ``4001``.  A timeout closes with ``1008``
    (policy violation).

    **Subsequent Client → Server messages:**
    ```json
    {"type": "location_update", "latitude": 55.7, "longitude": 37.6}
    {"type": "pong"}
    ```

    **Server → Client events:**
    ```json
    {"type": "message_new",          "data": { ...MessageResponse }}
    {"type": "reaction_added",       "data": {"message_id": "...", "new_count": 5}}
    {"type": "nearby_count_changed", "data": {"count": 3}}
    {"type": "ping"}
    ```
    """
    # ── Step 1: Accept the TCP connection ──────────────────────────────────────
    await websocket.accept()

    # ── Step 2: Authenticate via first message ─────────────────────────────────
    user_id, latitude, longitude = await _authenticate(websocket)
    if user_id is None:
        return  # _authenticate already closed the connection

    manager: ConnectionManager = websocket.app.state.ws_manager

    # ── Step 3: Register connection ────────────────────────────────────────────
    await manager.connect(websocket, user_id, latitude, longitude)

    # Notify nearby peers about the new user
    if latitude is not None and longitude is not None:
        asyncio.create_task(
            manager.broadcast_nearby_count(latitude, longitude, radius_meters=100)
        )

    # ── Step 4: Ping loop ──────────────────────────────────────────────────────
    async def _ping_loop() -> None:
        while True:
            await asyncio.sleep(_PING_INTERVAL)
            try:
                await websocket.send_json({"type": "ping"})
                manager.record_ping(user_id)
            except Exception:
                break

    ping_task = asyncio.create_task(_ping_loop())

    # ── Step 5: Message loop ───────────────────────────────────────────────────
    entry_lat = latitude
    entry_lng = longitude

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "location_update":
                try:
                    loc = WsLocationUpdateMessage(**msg)
                except ValidationError:
                    continue

                # Rate-limit: 1 location update per minute per user
                if not rate_limiter.is_allowed(
                    f"location_update:{user_id}",
                    limit=settings.RATE_LIMIT_LOCATION_UPDATES,
                    window_seconds=settings.RATE_LIMIT_LOCATION_WINDOW_SECONDS,
                ):
                    await websocket.send_json(
                        {"type": "error", "code": "rate_limited", "detail": "Too many location updates"}
                    )
                    continue

                manager.update_location(user_id, loc.latitude, loc.longitude)
                entry_lat = loc.latitude
                entry_lng = loc.longitude
                asyncio.create_task(
                    manager.broadcast_nearby_count(loc.latitude, loc.longitude, radius_meters=100)
                )

            elif msg_type == "pong":
                manager.record_ping(user_id)

    except WebSocketDisconnect:
        pass
    finally:
        ping_task.cancel()
        manager.disconnect(user_id)
        # Broadcast updated count after disconnect
        if entry_lat is not None and entry_lng is not None:
            asyncio.create_task(
                manager.broadcast_nearby_count(entry_lat, entry_lng, radius_meters=100)
            )


async def _authenticate(websocket: WebSocket) -> tuple[Optional[str], Optional[float], Optional[float]]:
    """Wait for the auth handshake and return ``(user_id, latitude, longitude)``.

    Returns ``(None, None, None)`` and closes the WebSocket on any failure.
    """
    try:
        raw = await asyncio.wait_for(
            websocket.receive_text(),
            timeout=settings.WS_AUTH_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("WebSocket auth timeout")
        await websocket.close(code=1008)  # Policy Violation
        return None, None, None
    except Exception:
        await websocket.close(code=1008)
        return None, None, None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        await websocket.close(code=4001)
        return None, None, None

    try:
        auth_msg = WsAuthMessage(**data)
    except ValidationError:
        await websocket.close(code=4001)
        return None, None, None

    payload = decode_token(auth_msg.token)
    if payload is None:
        await websocket.close(code=4001)
        return None, None, None

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001)
        return None, None, None

    return user_id, auth_msg.latitude, auth_msg.longitude
