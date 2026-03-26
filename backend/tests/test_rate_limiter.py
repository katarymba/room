"""Unit tests for the in-memory rate limiter."""
import time
import pytest
from unittest.mock import patch

from app.rate_limiter import RateLimiter


class TestRateLimiter:
    def setup_method(self):
        self.rl = RateLimiter()

    # ── Basic allow / deny ────────────────────────────────────────────────────

    def test_first_request_is_allowed(self):
        assert self.rl.is_allowed("op:user1", limit=5, window_seconds=60) is True

    def test_requests_within_limit_are_allowed(self):
        for _ in range(5):
            assert self.rl.is_allowed("op:user2", limit=5, window_seconds=60) is True

    def test_request_exceeding_limit_is_denied(self):
        for _ in range(5):
            self.rl.is_allowed("op:user3", limit=5, window_seconds=60)
        assert self.rl.is_allowed("op:user3", limit=5, window_seconds=60) is False

    def test_different_keys_are_independent(self):
        for _ in range(3):
            self.rl.is_allowed("op:user-a", limit=3, window_seconds=60)
        # user-a is exhausted; user-b should still be allowed
        assert self.rl.is_allowed("op:user-b", limit=3, window_seconds=60) is True
        assert self.rl.is_allowed("op:user-a", limit=3, window_seconds=60) is False

    def test_limit_one_allows_exactly_one(self):
        assert self.rl.is_allowed("loc:user4", limit=1, window_seconds=60) is True
        assert self.rl.is_allowed("loc:user4", limit=1, window_seconds=60) is False

    # ── Sliding window expiry ─────────────────────────────────────────────────

    def test_requests_allowed_after_window_expires(self):
        key = "op:user5"
        # Fill the window
        assert self.rl.is_allowed(key, limit=1, window_seconds=1) is True
        assert self.rl.is_allowed(key, limit=1, window_seconds=1) is False

        # Advance time past the window
        future = time.monotonic() + 2
        with patch("app.rate_limiter.time") as mock_time:
            mock_time.monotonic.return_value = future
            # Window has expired; should be allowed again
            assert self.rl.is_allowed(key, limit=1, window_seconds=1) is True

    # ── Reset ─────────────────────────────────────────────────────────────────

    def test_reset_clears_key(self):
        key = "op:user6"
        for _ in range(3):
            self.rl.is_allowed(key, limit=3, window_seconds=60)
        assert self.rl.is_allowed(key, limit=3, window_seconds=60) is False
        self.rl.reset(key)
        assert self.rl.is_allowed(key, limit=3, window_seconds=60) is True

    def test_reset_nonexistent_key_is_safe(self):
        self.rl.reset("does-not-exist")  # must not raise
