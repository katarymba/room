"""Payments service — Stripe (web) and RevenueCat (mobile) integration.

The Stripe secret key and webhook secret must be supplied via environment
variables.  When they are absent the endpoints return 503 so the rest of the
application continues to function normally.
"""
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_PREMIUM_MONTHLY_PRICE_ID = os.getenv("STRIPE_MONTHLY_PRICE_ID", "")
_PREMIUM_YEARLY_PRICE_ID = os.getenv("STRIPE_YEARLY_PRICE_ID", "")


# ── Stripe helpers ────────────────────────────────────────────────────────────


def _get_stripe():
    """Return the stripe module configured with the secret key, or ``None``."""
    secret = os.getenv("STRIPE_SECRET_KEY", "")
    if not secret:
        return None
    try:
        import stripe  # type: ignore

        stripe.api_key = secret
        return stripe
    except ImportError:
        logger.warning("stripe package not installed; payment endpoints disabled")
        return None


def create_checkout_session(
    user_id: str,
    plan: str = "monthly",
    success_url: str = "",
    cancel_url: str = "",
) -> Optional[str]:
    """Create a Stripe Checkout session and return its URL.

    Returns ``None`` when Stripe is not configured.
    """
    stripe = _get_stripe()
    if stripe is None:
        return None

    price_id = _PREMIUM_MONTHLY_PRICE_ID if plan == "monthly" else _PREMIUM_YEARLY_PRICE_ID
    if not price_id:
        logger.warning("Stripe price ID not configured for plan=%s", plan)
        return None

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            client_reference_id=user_id,
            success_url=success_url or os.getenv("STRIPE_SUCCESS_URL", ""),
            cancel_url=cancel_url or os.getenv("STRIPE_CANCEL_URL", ""),
        )
        return session.url
    except Exception as exc:
        logger.error("Stripe checkout error: %s", exc)
        return None


def verify_stripe_webhook(payload: bytes, sig_header: str) -> Optional[dict]:
    """Validate a Stripe webhook signature and return the parsed event.

    Returns ``None`` if the signature is invalid or Stripe is not configured.
    """
    stripe = _get_stripe()
    if stripe is None:
        return None

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET not set; webhook validation skipped")
        return None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        return event
    except Exception as exc:
        logger.warning("Stripe webhook verification failed: %s", exc)
        return None


def handle_stripe_event(event: dict, db) -> None:
    """Process a verified Stripe webhook event and update the database."""
    from app.models.user import User

    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        user_id = data_object.get("client_reference_id")
        if user_id:
            _activate_premium(db, user_id, months=1)

    elif event_type == "invoice.payment_succeeded":
        # Recurring renewal — find user by customer ID
        customer_id = data_object.get("customer")
        if customer_id:
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                _activate_premium(db, str(user.id), months=1)

    elif event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
        customer_id = data_object.get("customer")
        if customer_id:
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                _deactivate_premium(db, str(user.id))


def verify_revenuecat_webhook(payload: bytes, auth_header: str) -> bool:
    """Validate a RevenueCat webhook using the shared secret.

    Returns ``True`` if the request is authentic.
    """
    secret = os.getenv("REVENUECAT_WEBHOOK_AUTH_HEADER", "")
    if not secret:
        logger.warning("REVENUECAT_WEBHOOK_AUTH_HEADER not set; webhook validation skipped")
        return False
    return hmac.compare_digest(auth_header, secret)


def handle_revenuecat_event(event: dict, db) -> None:
    """Process a RevenueCat webhook event."""
    from app.models.user import User

    event_type = event.get("type", "")
    app_user_id = event.get("app_user_id") or event.get("original_app_user_id")

    if not app_user_id:
        return

    if event_type in ("INITIAL_PURCHASE", "RENEWAL", "PRODUCT_CHANGE"):
        _activate_premium(db, app_user_id, months=1)
    elif event_type in ("EXPIRATION", "CANCELLATION", "BILLING_ISSUE"):
        _deactivate_premium(db, app_user_id)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _activate_premium(db, user_id: str, months: int = 1) -> None:
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    user.tier = "premium"
    user.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=30 * months)
    db.commit()
    logger.info("User %s upgraded to premium (expires %s)", user_id, user.subscription_expires_at)

def _deactivate_premium(db, user_id: str) -> None:
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    user.tier = "free"
    user.subscription_expires_at = None
    db.commit()
    logger.info("User %s downgraded to free tier", user_id)
