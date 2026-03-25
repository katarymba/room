"""WebSocket router — real-time room events."""
import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import decode_token
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()

# The global manager is injected from main.py via app.state
_PING_INTERVAL = 30  # seconds


async def _get_manager(websocket: WebSocket) -> ConnectionManager:
    return websocket.app.state.ws_manager


@router.websocket("/room")
async def websocket_room(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time room events.

    Authentication: pass JWT as ``?token=<jwt>``.

    **Client → Server messages:**
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
    # ── Authenticate ─────────────────────────────────────────────────────────
    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=4001)
        return

    user_id: str = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001)
        return

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
                    manager.update_location(user_id, float(lat), float(lng))
                    asyncio.create_task(
                        manager.broadcast_nearby_count(float(lat), float(lng), radius_meters=100)
                    )

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
