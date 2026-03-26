"""FastAPI application entry point."""
import logging
import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, room, chat, location
from app.routers import websocket as ws_router
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)

# ── Sentry (optional) ─────────────────────────────────────────────────────────
_SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if _SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            environment=os.getenv("ENVIRONMENT", "development"),
            traces_sample_rate=0.1,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        )
        logger.info("Sentry initialised (env=%s)", os.getenv("ENVIRONMENT", "development"))
    except ImportError:
        logger.warning("sentry-sdk not installed; error tracking disabled")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Room — anonymous location-based chat application",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Global WebSocket connection manager (in-memory for MVP)
app.state.ws_manager = ConnectionManager()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(room.router, prefix="/api/room", tags=["Room"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(ws_router.router, prefix="/ws", tags=["WebSocket"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


# ── Subscription / Payments ───────────────────────────────────────────────────


@app.post("/api/subscribe", tags=["Payments"])
async def subscribe(
    request: Request,
    plan: str = "monthly",
    current_user=None,
):
    """Initiate a Stripe Checkout session for a premium subscription."""
    from app.services.auth import get_current_user
    from app.database import get_db

    # Resolve dependencies manually for simplicity
    db_gen = get_db()
    db = next(db_gen)
    try:
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        from fastapi import Depends
        from app.services.auth import decode_access_token

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        token = auth_header.split(" ", 1)[1]
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        from app.payments import create_checkout_session

        checkout_url = create_checkout_session(
            user_id=user_id,
            plan=plan,
            success_url=f"{request.base_url}api/subscription/status",
            cancel_url=str(request.base_url),
        )
        if checkout_url is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service not configured",
            )
        return {"checkout_url": checkout_url}
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.post("/api/webhooks/stripe", tags=["Payments"])
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    from app.payments import verify_stripe_webhook, handle_stripe_event
    from app.database import get_db

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    event = verify_stripe_webhook(payload, sig_header)
    if event is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook")

    db_gen = get_db()
    db = next(db_gen)
    try:
        handle_stripe_event(event, db)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

    return {"received": True}


@app.post("/api/webhooks/revenuecat", tags=["Payments"])
async def revenuecat_webhook(request: Request):
    """Handle RevenueCat webhook events."""
    from app.payments import verify_revenuecat_webhook, handle_revenuecat_event
    from app.database import get_db

    payload = await request.body()
    auth_header = request.headers.get("Authorization", "")

    if not verify_revenuecat_webhook(payload, auth_header):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook auth")

    import json
    try:
        event = json.loads(payload)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    db_gen = get_db()
    db = next(db_gen)
    try:
        handle_revenuecat_event(event, db)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

    return {"received": True}


@app.get("/api/subscription/status", tags=["Payments"])
async def subscription_status(request: Request):
    """Check the current user's subscription status."""
    from app.services.auth import decode_access_token
    from app.database import get_db
    from app.models.user import User

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    db_gen = get_db()
    db = next(db_gen)
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return {
            "tier": user.tier,
            "subscription_expires_at": user.subscription_expires_at,
            "daily_message_count": user.daily_message_count,
        }
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
