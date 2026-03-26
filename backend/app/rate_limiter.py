"""In-memory sliding-window rate limiter.

Designed to be used as a single process-level singleton for the WebSocket
and REST API layers.  A Redis-backed implementation can be swapped in for
production deployments with multiple workers by replacing *RateLimiter* with
a Redis-aware variant that shares state across processes.

Usage example::

    rate_limiter = RateLimiter()

    if not rate_limiter.is_allowed("location_update:user-123", limit=1, window_seconds=60):
        # reject the request
        ...
"""
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict


class RateLimiter:
    """Sliding-window rate limiter backed by an in-memory store.

    Thread-safe via a reentrant lock; suitable for single-process deployments.
    For multi-process deployments, replace with a Redis-backed implementation.
    """

    def __init__(self) -> None:
        # key -> deque of monotonic timestamps (seconds)
        self._windows: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Return *True* if the request is within the rate limit, *False* otherwise.

        :param key:            Unique key for this (user, operation) pair.
                               Convention: ``"<operation>:<user_id>"``.
        :param limit:          Maximum number of requests allowed in *window_seconds*.
        :param window_seconds: Duration of the sliding window in seconds.
        """
        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            window = self._windows[key]

            # Remove timestamps that have fallen outside the window
            while window and window[0] <= cutoff:
                window.popleft()

            if len(window) >= limit:
                return False

            window.append(now)
            return True

    def reset(self, key: str) -> None:
        """Clear all recorded events for *key* (useful in tests)."""
        with self._lock:
            self._windows.pop(key, None)


# Process-level singleton — import and use directly
rate_limiter = RateLimiter()
