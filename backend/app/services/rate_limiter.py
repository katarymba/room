"""Rate limiting service — in-memory with optional Redis backend.

Limits enforced:
  - Free users: 20 messages/day, 100 reactions/hour, 10 connections/hour
  - Premium users: unlimited messages, 1000 reactions/hour, 100 connections/hour
  - All users: 5 messages/10 sec, 10 reactions/10 sec (anti-spam)
  - Login: 5 attempts/minute per phone/IP
"""
import time
import logging
from collections import defaultdict
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

FREE_USER_LIMITS: Dict[str, int] = {
    "messages_per_day": 20,
    "reactions_per_hour": 100,
    "connections_per_hour": 10,
}

PREMIUM_USER_LIMITS: Dict[str, int] = {
    "messages_per_day": -1,  # unlimited
    "reactions_per_hour": 1000,
    "connections_per_hour": 100,
}

# Short-window anti-spam limits (applied to all tiers)
SHORT_WINDOW_LIMITS: Dict[str, int] = {
    "messages_per_10s": 5,
    "reactions_per_10s": 10,
    "login_per_minute": 5,
}

_DAY_SECONDS = 86_400
_HOUR_SECONDS = 3_600
_MINUTE_SECONDS = 60
_SHORT_WINDOW_SECONDS = 10

# ── In-memory store ───────────────────────────────────────────────────────────
# Structure: {key: (count, window_start_ts)}
_store: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))


def _get_limit(tier: str, action: str) -> int:
    """Return the rate limit for *action* given the user *tier*."""
    if action in SHORT_WINDOW_LIMITS:
        return SHORT_WINDOW_LIMITS[action]
    limits = PREMIUM_USER_LIMITS if tier == "premium" else FREE_USER_LIMITS
    return limits.get(action, -1)


def _window_seconds(action: str) -> int:
    if action == "messages_per_day":
        return _DAY_SECONDS
    if action in ("reactions_per_hour", "connections_per_hour"):
        return _HOUR_SECONDS
    if action in ("messages_per_10s", "reactions_per_10s"):
        return _SHORT_WINDOW_SECONDS
    if action == "login_per_minute":
        return _MINUTE_SECONDS
    return _HOUR_SECONDS


def check_rate_limit(user_id: str, tier: str, action: str) -> Tuple[bool, int]:
    """Check whether *user_id* is within the rate limit for *action*.

    Returns ``(allowed, remaining)`` where *remaining* is the number of
    remaining allowed actions in the current window (``-1`` = unlimited).

    The in-memory counter is automatically reset when the window expires.
    """
    limit = _get_limit(tier, action)
    if limit == -1:
        return True, -1  # unlimited

    window = _window_seconds(action)
    key = f"{user_id}:{action}"
    count, window_start = _store[key]

    now = time.time()
    if now - window_start >= window:
        # Window has expired — reset
        count = 0
        window_start = now

    allowed = count < limit
    if allowed:
        _store[key] = (count + 1, window_start)

    remaining = max(0, limit - count - 1) if allowed else 0
    return allowed, remaining


def reset_counter(user_id: str, action: str) -> None:
    """Reset the rate limit counter for *user_id* and *action* (useful in tests)."""
    key = f"{user_id}:{action}"
    _store[key] = (0, time.time())


def get_current_count(user_id: str, action: str) -> int:
    """Return the current counter value without incrementing it."""
    key = f"{user_id}:{action}"
    count, window_start = _store[key]
    window = _window_seconds(action)
    if time.time() - window_start >= window:
        return 0
    return count
