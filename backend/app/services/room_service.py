"""Room service — business logic for mystery mode and author reveal."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.reaction import Reaction

# Author is automatically revealed after this many hours
_REVEAL_AFTER_HOURS = 24


def check_author_reveal(
    db: Session,
    message: Message,
    current_user_id: UUID,
) -> bool:
    """
    Determine whether the message author should be revealed to *current_user_id*.

    An author is revealed if **any** of these conditions is met:

    1. **Mutual reaction:** The current user has liked the message *and* the
       message author has liked at least one message written by the current
       user.
    2. **Time elapsed:** The message was created more than 24 hours ago.
    3. **Own message:** The current user is the author.

    When revealed for the first time this function also persists
    *current_user_id* into ``message.revealed_to`` so future calls are cheap.
    """
    # Own messages are always "revealed"
    if str(message.user_id) == str(current_user_id):
        return True

    # Already revealed
    revealed_to = message.revealed_to or []
    if _uuid_in_list(current_user_id, revealed_to):
        return True

    # Condition 2: older than 24 hours
    if datetime.utcnow() - message.created_at > timedelta(hours=_REVEAL_AFTER_HOURS):
        _mark_revealed(db, message, current_user_id)
        return True

    # Condition 1: mutual reaction
    if _has_mutual_reaction(db, message, current_user_id):
        _mark_revealed(db, message, current_user_id)
        return True

    return False


# ── Private helpers ───────────────────────────────────────────────────────────


def _has_mutual_reaction(db: Session, message: Message, current_user_id: UUID) -> bool:
    """Return True if both users have liked each other's messages."""
    # Current user liked this message
    user_liked_message = (
        db.query(Reaction)
        .filter(
            Reaction.message_id == message.id,
            Reaction.user_id == current_user_id,
        )
        .first()
    )
    if not user_liked_message:
        return False

    # Author liked at least one message by the current user
    author_liked_back = (
        db.query(Reaction)
        .join(Message, Reaction.message_id == Message.id)
        .filter(
            Reaction.user_id == message.user_id,
            Message.user_id == current_user_id,
        )
        .first()
    )
    return author_liked_back is not None


def _mark_revealed(db: Session, message: Message, current_user_id: UUID) -> None:
    """Persist *current_user_id* in ``message.revealed_to``."""
    try:
        revealed = list(message.revealed_to or [])
        if not _uuid_in_list(current_user_id, revealed):
            revealed.append(current_user_id)
            message.revealed_to = revealed
            db.add(message)
            db.commit()
    except Exception:
        db.rollback()


def _uuid_in_list(target: UUID, items: list) -> bool:
    target_str = str(target)
    return any(str(item) == target_str for item in items)
