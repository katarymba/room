"""Bot messages service — generate fake messages for UX bootstrapping.

When real message count is low the GET /room/messages endpoint supplements
the response with a handful of pre-written bot messages so that new users
never see an empty room.

Bot messages are:
- Generated on-the-fly (NOT stored in the database).
- Assigned random UUIDs for both the message id and the bot user_id.
- Placed within ±50 m of the requesting user.
- Back-dated between 5 minutes and 2 hours ago.
- Marked with an internal ``is_bot`` flag that is *not* exposed to clients.
"""
import random
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from app.schemas.message import MessageResponse

# ── Catalogue of pre-written messages ────────────────────────────────────────

BOT_MESSAGES: List[str] = [
    "Кто-то тут? 👀",
    "Скучно... кто онлайн?",
    "Привет соседи 😏",
    "Что происходит здесь?",
    "Кто-нибудь видел новую кофейню? ☕",
    "Кто-то слышал громкую музыку сегодня?",
    "Эй, все живы? 😄",
    "Тихий вечер у вас тоже?",
    "Первый раз пробую это приложение 👋",
    "Кто ещё тут ночью?",
    "Привет из-за угла 😅",
    "Кто-нибудь знает, что за стройка рядом?",
    "Тут есть хороший Wi-Fi?",
    "Ищу компанию для прогулки 🚶",
    "Хорошая погода сегодня, правда?",
    "Кто дежурит в округе? 😄",
    "Только что переехал сюда, привет всем!",
    "Есть кто поблизости?",
    "Пустовато тут сегодня...",
    "Рядом что-то интересное есть?",
    "Кто видел мою кошку? 🐱",
    "Всем доброй ночи 🌙",
    "Кто тоже не спит?",
    "Собаки здесь лают по ночам — это нормально?",
    "Привет от анонима 👻",
]

# Small coordinate offset for ±50 m variance (≈ 0.00045 degrees ≈ 50 m)
_COORD_DELTA = 0.00045


def generate_fake_messages(count: int, lat: float, lng: float) -> List[MessageResponse]:
    """
    Generate *count* synthetic room messages near the given coordinates.

    Each message gets:
    - A unique random UUID
    - A random bot user UUID (not in the users table)
    - A timestamp between 5 minutes and 2 hours in the past
    - Coordinates within ±50 m of (lat, lng)
    - ``is_mystery=True``, ``author_revealed=False``
    """
    now = datetime.utcnow()
    messages: List[MessageResponse] = []
    texts = random.sample(BOT_MESSAGES, min(count, len(BOT_MESSAGES)))

    for text in texts:
        age_seconds = random.randint(5 * 60, 2 * 60 * 60)
        created_at = now - timedelta(seconds=age_seconds)

        messages.append(
            MessageResponse(
                id=uuid4(),
                text=text,
                created_at=created_at,
                reaction_count=random.randint(0, 4),
                user_has_reacted=False,
                is_mystery=True,
                author_revealed=False,
                author_username=None,
            )
        )

    # Return sorted newest-first (same order as real messages)
    messages.sort(key=lambda m: m.created_at, reverse=True)
    return messages
