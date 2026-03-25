"""Room router — nearby users and messages endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.message import Message
from app.models.reaction import Reaction
from app.schemas.message import MessageCreate, MessageResponse, NearbyMessagesRequest
from app.schemas.reaction import ReactionCreate, ReactionResponse
from app.services.auth import get_current_user
from app.services.geo import get_nearby_messages, get_nearby_user_count

router = APIRouter()


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
        result.append(
            MessageResponse(
                id=msg.id,
                text=msg.text,
                created_at=msg.created_at,
                reaction_count=reaction_count,
                user_has_reacted=user_reacted,
            )
        )
    return result


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def post_room_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post an anonymous message to the room."""
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point

    point = from_shape(Point(message_data.longitude, message_data.latitude), srid=4326)
    message = Message(
        user_id=current_user.id,
        text=message_data.text,
        location=point,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return MessageResponse(
        id=message.id,
        text=message.text,
        created_at=message.created_at,
        reaction_count=0,
        user_has_reacted=False,
    )


@router.post("/reactions", response_model=ReactionResponse, status_code=status.HTTP_201_CREATED)
async def add_reaction(
    reaction_data: ReactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a reaction to a room message."""
    message = db.query(Message).filter(Message.id == reaction_data.message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

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
