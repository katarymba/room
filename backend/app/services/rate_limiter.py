"""Rate limiting service — in-memory with optional Redis backend.

Limits enforced:
  - Free users: 20 messages/day, 100 reactions/hour, 10 connections/hour
  - Premium users: unlimited messages, 1 000 reactions/hour, 100 connections/hour
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

_DAY_SECONDS = 86_400
_HOUR_SECONDS = 3_600

# ── In-memory store ───────────────────────────────────────────────────────────
# Structure: {key: (count, window_start_ts)}
_store: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))


def _get_limit(tier: str, action: str) -> int:
    """Return the rate limit for *action* given the user *tier*."""
    limits = PREMIUM_USER_LIMITS if tier == "premium" else FREE_USER_LIMITS
    return limits.get(action, -1)


def _window_seconds(action: str) -> int:
    if action == "messages_per_day":
        return _DAY_SECONDS
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
