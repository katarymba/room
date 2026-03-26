"""Tests for the rate limiting service."""
import time
import pytest

from app.services.rate_limiter import (
    FREE_USER_LIMITS,
    PREMIUM_USER_LIMITS,
    check_rate_limit,
    get_current_count,
    reset_counter,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _reset_all(user_id: str) -> None:
    for action in ("messages_per_day", "reactions_per_hour", "connections_per_hour"):
        reset_counter(user_id, action)


# ── Free-tier limits ──────────────────────────────────────────────────────────


class TestFreeUserMessageLimit:
    """Free users should be limited to 20 messages/day."""

    def setup_method(self):
        self.user_id = "test-free-msg-user"
        _reset_all(self.user_id)

    def test_first_message_is_allowed(self):
        allowed, remaining = check_rate_limit(self.user_id, "free", "messages_per_day")
        assert allowed is True
        assert remaining == FREE_USER_LIMITS["messages_per_day"] - 1

    def test_message_limit_is_enforced(self):
        limit = FREE_USER_LIMITS["messages_per_day"]
        for _ in range(limit):
            allowed, _ = check_rate_limit(self.user_id, "free", "messages_per_day")
            assert allowed is True

        # Next call should be denied
        allowed, remaining = check_rate_limit(self.user_id, "free", "messages_per_day")
        assert allowed is False
        assert remaining == 0

    def test_counter_increments(self):
        check_rate_limit(self.user_id, "free", "messages_per_day")
        assert get_current_count(self.user_id, "messages_per_day") == 1
        check_rate_limit(self.user_id, "free", "messages_per_day")
        assert get_current_count(self.user_id, "messages_per_day") == 2

    def test_reset_clears_counter(self):
        check_rate_limit(self.user_id, "free", "messages_per_day")
        reset_counter(self.user_id, "messages_per_day")
        assert get_current_count(self.user_id, "messages_per_day") == 0


class TestFreeUserReactionLimit:
    """Free users should be limited to 100 reactions/hour."""

    def setup_method(self):
        self.user_id = "test-free-react-user"
        _reset_all(self.user_id)

    def test_reactions_within_limit_are_allowed(self):
        for _ in range(10):
            allowed, _ = check_rate_limit(self.user_id, "free", "reactions_per_hour")
            assert allowed is True

    def test_reaction_limit_is_enforced(self):
        limit = FREE_USER_LIMITS["reactions_per_hour"]
        for _ in range(limit):
            check_rate_limit(self.user_id, "free", "reactions_per_hour")

        allowed, _ = check_rate_limit(self.user_id, "free", "reactions_per_hour")
        assert allowed is False


# ── Premium-tier limits ───────────────────────────────────────────────────────


class TestPremiumUserMessageLimit:
    """Premium users have unlimited messages."""

    def setup_method(self):
        self.user_id = "test-premium-msg-user"
        _reset_all(self.user_id)

    def test_messages_are_unlimited(self):
        # Call well beyond the free limit
        for _ in range(FREE_USER_LIMITS["messages_per_day"] + 50):
            allowed, remaining = check_rate_limit(self.user_id, "premium", "messages_per_day")
            assert allowed is True
            assert remaining == -1  # unlimited


class TestPremiumUserReactionLimit:
    """Premium users have 1000 reactions/hour."""

    def setup_method(self):
        self.user_id = "test-premium-react-user"
        _reset_all(self.user_id)

    def test_reactions_within_premium_limit_are_allowed(self):
        for _ in range(FREE_USER_LIMITS["reactions_per_hour"] + 50):
            allowed, _ = check_rate_limit(self.user_id, "premium", "reactions_per_hour")
            assert allowed is True


# ── Connection rate limit ─────────────────────────────────────────────────────


class TestConnectionRateLimit:
    def setup_method(self):
        self.key = "test-conn-ip-192.168.1.1"
        _reset_all(self.key)

    def test_connections_within_limit(self):
        for _ in range(FREE_USER_LIMITS["connections_per_hour"]):
            allowed, _ = check_rate_limit(self.key, "free", "connections_per_hour")
            assert allowed is True

    def test_connection_limit_is_enforced(self):
        limit = FREE_USER_LIMITS["connections_per_hour"]
        for _ in range(limit):
            check_rate_limit(self.key, "free", "connections_per_hour")

        allowed, _ = check_rate_limit(self.key, "free", "connections_per_hour")
        assert allowed is False


# ── User isolation ────────────────────────────────────────────────────────────


class TestUserIsolation:
    """Rate limit counters must not bleed across users."""

    def setup_method(self):
        self.user_a = "isolation-user-a"
        self.user_b = "isolation-user-b"
        _reset_all(self.user_a)
        _reset_all(self.user_b)

    def test_counters_are_independent(self):
        limit = FREE_USER_LIMITS["messages_per_day"]
        # Exhaust user_a's limit
        for _ in range(limit):
            check_rate_limit(self.user_a, "free", "messages_per_day")

        # user_b should still be allowed
        allowed, _ = check_rate_limit(self.user_b, "free", "messages_per_day")
        assert allowed is True
