"""Analytics service — event tracking with Mixpanel/PostHog integration.

Falls back to structured logging when no analytics backend is configured so
that the application always starts correctly without external dependencies.

Set ``MIXPANEL_TOKEN`` or ``POSTHOG_API_KEY`` in the environment to enable
real tracking.
"""
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Event name constants ──────────────────────────────────────────────────────

EVENT_MESSAGE_SENT = "message_sent"
EVENT_MESSAGE_REVEALED = "message_revealed"
EVENT_REACTION_ADDED = "reaction_added"
EVENT_USER_REGISTERED = "user_registered"
EVENT_SUBSCRIPTION_STARTED = "subscription_started"
EVENT_SUBSCRIPTION_CANCELLED = "subscription_cancelled"
EVENT_PAYWALL_SHOWN = "paywall_shown"
EVENT_PAYWALL_DISMISSED = "paywall_dismissed"
EVENT_WS_CONNECTED = "ws_connected"
EVENT_WS_DISCONNECTED = "ws_disconnected"
EVENT_RATE_LIMIT_HIT = "rate_limit_hit"


# ── Backend helpers ───────────────────────────────────────────────────────────


def _get_mixpanel():
    """Return a Mixpanel client if configured, else ``None``."""
    token = os.getenv("MIXPANEL_TOKEN", "")
    if not token:
        return None
    try:
        from mixpanel import Mixpanel  # type: ignore

        return Mixpanel(token)
    except ImportError:
        logger.warning("mixpanel package not installed; analytics disabled")
        return None


# ── Public API ────────────────────────────────────────────────────────────────


class Analytics:
    """Lightweight analytics wrapper.

    All methods are safe to call even when no backend is configured — they
    will fall back to structured log output so you still get observability.
    """

    def __init__(self) -> None:
        self._mp = None  # lazily initialised

    def _mixpanel(self):
        if self._mp is None:
            self._mp = _get_mixpanel()
        return self._mp

    def track_event(
        self,
        user_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a named event for *user_id* with optional *properties*."""
        props = properties or {}
        mp = self._mixpanel()
        if mp is not None:
            try:
                mp.track(user_id, event_name, props)
                return
            except Exception as exc:
                logger.warning("Mixpanel track_event error: %s", exc)

        # Fallback: structured log
        logger.info(
            "analytics event=%s user=%s props=%s",
            event_name,
            user_id,
            props,
        )

    def track_user_property(
        self,
        user_id: str,
        property_name: str,
        value: Any,
    ) -> None:
        """Set a user-level property for *user_id*."""
        mp = self._mixpanel()
        if mp is not None:
            try:
                mp.people_set(user_id, {property_name: value})
                return
            except Exception as exc:
                logger.warning("Mixpanel people_set error: %s", exc)

        logger.info("analytics user_property user=%s %s=%s", user_id, property_name, value)

    # ── Convenience wrappers ──────────────────────────────────────────────────

    def message_sent(self, user_id: str, is_mystery: bool, has_location: bool) -> None:
        self.track_event(
            user_id,
            EVENT_MESSAGE_SENT,
            {"is_mystery": is_mystery, "has_location": has_location},
        )

    def reaction_added(self, user_id: str, reaction_type: str) -> None:
        self.track_event(user_id, EVENT_REACTION_ADDED, {"reaction_type": reaction_type})

    def user_registered(self, user_id: str, method: str = "device") -> None:
        self.track_event(user_id, EVENT_USER_REGISTERED, {"method": method})

    def subscription_started(self, user_id: str, plan: str) -> None:
        self.track_event(user_id, EVENT_SUBSCRIPTION_STARTED, {"plan": plan})
        self.track_user_property(user_id, "tier", "premium")

    def subscription_cancelled(self, user_id: str, plan: str) -> None:
        self.track_event(user_id, EVENT_SUBSCRIPTION_CANCELLED, {"plan": plan})
        self.track_user_property(user_id, "tier", "free")

    def paywall_shown(self, user_id: str, trigger: str = "limit_reached") -> None:
        self.track_event(user_id, EVENT_PAYWALL_SHOWN, {"trigger": trigger})

    def rate_limit_hit(self, user_id: str, action: str) -> None:
        self.track_event(user_id, EVENT_RATE_LIMIT_HIT, {"action": action})


# Singleton instance used throughout the app
analytics = Analytics()
