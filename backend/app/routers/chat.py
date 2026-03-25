"""Chat router — private chat endpoints."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database import get_db
from app.models.user import User
from app.models.chat import Chat, ChatMessage
from app.models.reaction import Reaction
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatResponse, ChatListResponse
from app.services.auth import get_current_user

router = APIRouter()


def _get_or_create_chat(db: Session, user1_id: UUID, user2_id: UUID) -> Chat:
    """Get existing chat or create a new one between two users."""
    chat = (
        db.query(Chat)
        .filter(
            or_(
                and_(Chat.user1_id == user1_id, Chat.user2_id == user2_id),
                and_(Chat.user1_id == user2_id, Chat.user2_id == user1_id),
            )
        )
        .first()
    )
    if not chat:
        chat = Chat(user1_id=user1_id, user2_id=user2_id)
        db.add(chat)
        db.commit()
        db.refresh(chat)
    return chat


def _check_mutual_interest(db: Session, user_id: UUID, other_user_id: UUID) -> bool:
    """Check if two users have mutual likes (reacted to each other's messages)."""
    # user liked a message from other_user
    from app.models.message import Message as RoomMessage

    user_liked_other = (
        db.query(Reaction)
        .join(RoomMessage, Reaction.message_id == RoomMessage.id)
        .filter(Reaction.user_id == user_id, RoomMessage.user_id == other_user_id)
        .first()
    )

    # other_user liked a message from user
    other_liked_user = (
        db.query(Reaction)
        .join(RoomMessage, Reaction.message_id == RoomMessage.id)
        .filter(Reaction.user_id == other_user_id, RoomMessage.user_id == user_id)
        .first()
    )

    return user_liked_other is not None and other_liked_user is not None


@router.get("/", response_model=ChatListResponse)
async def list_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all private chats for the current user."""
    chats = (
        db.query(Chat)
        .filter(or_(Chat.user1_id == current_user.id, Chat.user2_id == current_user.id))
        .all()
    )

    result = []
    for chat in chats:
        other_id = chat.user2_id if str(chat.user1_id) == str(current_user.id) else chat.user1_id
        last_msg = (
            db.query(ChatMessage)
            .filter(ChatMessage.chat_id == chat.id)
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        result.append(
            ChatResponse(
                id=chat.id,
                created_at=chat.created_at,
                other_user_id=other_id,
                last_message=last_msg.text if last_msg else None,
                last_message_at=last_msg.created_at if last_msg else None,
            )
        )

    return ChatListResponse(chats=result, total=len(result))


@router.post("/open/{other_user_id}", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def open_chat(
    other_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Open a private chat with another user (requires mutual interest)."""
    if str(other_user_id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot chat with yourself")

    other_user = db.query(User).filter(User.id == other_user_id).first()
    if not other_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verify mutual interest (both liked each other's messages)
    if not _check_mutual_interest(db, current_user.id, other_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mutual interest required to open a chat",
        )

    chat = _get_or_create_chat(db, current_user.id, other_user_id)
    return ChatResponse(
        id=chat.id,
        created_at=chat.created_at,
        other_user_id=other_user_id,
    )


@router.get("/{chat_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    chat_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages in a private chat."""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    # Verify the current user is a participant
    if str(chat.user1_id) != str(current_user.id) and str(chat.user2_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        ChatMessageResponse(
            id=msg.id,
            chat_id=msg.chat_id,
            sender_id=msg.sender_id,
            text=msg.text,
            created_at=msg.created_at,
            is_mine=str(msg.sender_id) == str(current_user.id),
        )
        for msg in messages
    ]


@router.post("/{chat_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    chat_id: UUID,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message in a private chat."""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    if str(chat.user1_id) != str(current_user.id) and str(chat.user2_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    message = ChatMessage(
        chat_id=chat_id,
        sender_id=current_user.id,
        text=message_data.text,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return ChatMessageResponse(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        text=message.text,
        created_at=message.created_at,
        is_mine=True,
    )
