"""Room router — nearby users and messages endpoints."""
import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.message import Message
from app.models.reaction import Reaction
from app.schemas.message import MessageCreate, MessageResponse, NearbyMessagesRequest
from app.schemas.reaction import ReactionCreate, ReactionResponse
from app.services.auth import get_current_user
from app.services.bot_messages import generate_fake_messages
from app.services.geo import get_nearby_messages, get_nearby_user_count
from app.services.rate_limiter import check_rate_limit
from app.services.room_service import check_author_reveal

router = APIRouter()

# Supplement with bot messages when real messages fall below this threshold
_MIN_MESSAGES = 3


@router.get("/nearby/users", response_model=dict)
async def get_nearby_users(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_meters: int = Query(default=100, ge=10, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get count of active users within specified radius."""
    count = get_nearby_user_count(db, latitude, longitude, radius_meters)
    return {"count": count, "radius_meters": radius_meters}


@router.get("/messages", response_model=List[MessageResponse])
async def get_room_messages(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_meters: int = Query(default=100, ge=10, le=200),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages from the current room (within radius)."""
    messages = get_nearby_messages(db, latitude, longitude, radius_meters, limit)

    result = []
    for msg in messages:
        reaction_count = db.query(Reaction).filter(Reaction.message_id == msg.id).count()
        user_reacted = (
            db.query(Reaction)
            .filter(Reaction.message_id == msg.id, Reaction.user_id == current_user.id)
            .first()
            is not None
        )
        revealed = check_author_reveal(db, msg, current_user.id)
        author_username: Optional[str] = None
        if revealed and msg.user:
            author_username = msg.user.phone or msg.user.device_id
        result.append(
            MessageResponse(
                id=msg.id,
                text=msg.text,
                created_at=msg.created_at,
                reaction_count=reaction_count,
                user_has_reacted=user_reacted,
                is_mystery=msg.is_mystery,
                author_revealed=revealed,
                author_username=author_username,
            )
        )

    # UX bootstrap: supplement with bot messages when there are too few real ones
    if len(result) < _MIN_MESSAGES:
        fake_count = _MIN_MESSAGES - len(result)
        fake_messages = generate_fake_messages(fake_count, latitude, longitude)
        result += fake_messages

    return result


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def post_room_message(
    request: Request,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post an anonymous message to the room."""
    import logging
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point

    _log = logging.getLogger(__name__)

    # ── Short-window anti-spam rate limit (5 msgs / 10 sec) ──────────────────
    allowed_short, _ = check_rate_limit(str(current_user.id), "any", "messages_per_10s")
    if not allowed_short:
        _log.warning("Message short-window rate limit exceeded for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many messages. Please slow down.",
            },
        )

    # ── Freemium daily rate limit ─────────────────────────────────────────────
    user_tier = current_user.tier or "free"
    allowed, remaining = check_rate_limit(str(current_user.id), user_tier, "messages_per_day")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Daily message limit reached. Upgrade to Premium for unlimited messages!",
                "paywall": True,
            },
        )

    # ── Anti-spam: duplicate message detection within 1 minute ───────────────
    from datetime import datetime, timedelta
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    duplicate = (
        db.query(Message)
        .filter(
            Message.user_id == current_user.id,
            Message.text == message_data.text,
            Message.created_at >= one_minute_ago,
        )
        .first()
    )
    if duplicate:
        _log.warning("Duplicate message attempt from user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "DUPLICATE_MESSAGE",
                "message": "Duplicate message. Please wait before sending the same message again.",
            },
        )

    point = from_shape(Point(message_data.longitude, message_data.latitude), srid=4326)
    message = Message(
        user_id=current_user.id,
        text=message_data.text,
        location=point,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    response = MessageResponse(
        id=message.id,
        text=message.text,
        created_at=message.created_at,
        reaction_count=0,
        user_has_reacted=False,
        is_mystery=message.is_mystery,
        author_revealed=True,  # sender always knows their own message
        author_username=None,
    )

    # Broadcast to nearby WebSocket clients
    ws_manager = getattr(request.app.state, "ws_manager", None)
    if ws_manager is not None:
        event = {"type": "message_new", "data": response.model_dump(mode="json")}
        asyncio.create_task(
            ws_manager.broadcast_to_nearby(
                event,
                message_data.latitude,
                message_data.longitude,
                radius_meters=100,
            )
        )

    return response


@router.post("/reactions", response_model=ReactionResponse, status_code=status.HTTP_201_CREATED)
async def add_reaction(
    request: Request,
    reaction_data: ReactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a reaction to a room message."""
    message = db.query(Message).filter(Message.id == reaction_data.message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # ── Short-window rate limit (10 reactions / 10 sec) ──────────────────────
    allowed_short, _ = check_rate_limit(str(current_user.id), "any", "reactions_per_10s")
    if not allowed_short:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many reactions. Please slow down.",
            },
        )

    # ── Reaction rate limit ───────────────────────────────────────────────────
    user_tier = current_user.tier or "free"
    allowed, _ = check_rate_limit(str(current_user.id), user_tier, "reactions_per_hour")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Reaction limit reached. Please try again later.",
            },
        )

    # Silently ignore reactions on bot messages — they have no DB record.
    # (Bot message UUIDs are random and won't match any DB row, so the 404
    # above already handles it; this comment documents intent.)

    # Check if reaction already exists
    existing = (
        db.query(Reaction)
        .filter(
            Reaction.message_id == reaction_data.message_id,
            Reaction.user_id == current_user.id,
            Reaction.reaction_type == reaction_data.reaction_type,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reaction already exists")

    reaction = Reaction(
        message_id=reaction_data.message_id,
        user_id=current_user.id,
        reaction_type=reaction_data.reaction_type,
    )
    db.add(reaction)
    db.commit()
    db.refresh(reaction)

    # Broadcast reaction update to nearby WebSocket clients
    new_count = db.query(Reaction).filter(Reaction.message_id == reaction_data.message_id).count()
    ws_manager = getattr(request.app.state, "ws_manager", None)
    if ws_manager is not None:
        from geoalchemy2.shape import to_shape

        try:
            point = to_shape(message.location)
            msg_lat, msg_lng = point.y, point.x
        except Exception:
            msg_lat, msg_lng = None, None

        if msg_lat is not None:
            event = {
                "type": "reaction_added",
                "data": {
                    "message_id": str(reaction_data.message_id),
                    "new_count": new_count,
                },
            }
            asyncio.create_task(
                ws_manager.broadcast_to_nearby(event, msg_lat, msg_lng, radius_meters=100)
            )

    return reaction


@router.delete("/reactions/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    message_id: UUID,
    reaction_type: str = Query(default="like"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a reaction from a room message."""
    reaction = (
        db.query(Reaction)
        .filter(
            Reaction.message_id == message_id,
            Reaction.user_id == current_user.id,
            Reaction.reaction_type == reaction_type,
        )
        .first()
    )
    if not reaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found")

    db.delete(reaction)
    db.commit()

