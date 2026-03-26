"""Authentication router — register, login, verify, refresh, logout endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    revoke_all_user_refresh_tokens,
    get_current_user,
)
from app.services.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Extract the client IP address from a request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or ""
    return ""


# ── Schemas ───────────────────────────────────────────────────────────────────


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/register/guest", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_guest(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new guest user using device_id."""
    if not user_data.device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="device_id is required for guest registration",
        )

    # Check if device already registered
    existing = db.query(User).filter(User.device_id == user_data.device_id).first()
    if existing:
        token = create_access_token({"sub": str(existing.id)})
        refresh = create_refresh_token(str(existing.id), db)
        response = TokenResponse(access_token=token, user=UserResponse.model_validate(existing))
        response.refresh_token = refresh
        return response

    # Create new guest user
    user = User(device_id=user_data.device_id)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token(str(user.id), db)
    response = TokenResponse(access_token=token, user=UserResponse.model_validate(user))
    response.refresh_token = refresh
    return response


@router.post("/register/phone", response_model=dict, status_code=status.HTTP_200_OK)
async def request_phone_verification(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """Request SMS verification code for phone-based authentication."""
    if not user_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="phone is required",
        )

    # Rate limit phone verification requests by IP
    client_ip = _get_client_ip(request)
    allowed, _ = check_rate_limit(f"phone_req:{client_ip}", "free", "login_per_min")
    if not allowed:
        logger.warning("Login rate limit exceeded for IP %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification requests. Please try again later.",
        )

    # In production, send SMS code via provider
    # For MVP, log the code or use a stub
    # TODO: integrate SMS provider (Twilio, etc.)
    return {"message": "Verification code sent", "phone": user_data.phone}


@router.post("/verify/phone", response_model=TokenResponse)
async def verify_phone(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Verify SMS code and authenticate user."""
    if not login_data.phone or not login_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="phone and code are required",
        )

    # Rate limit verification attempts by IP
    client_ip = _get_client_ip(request)
    allowed, _ = check_rate_limit(f"verify:{client_ip}", "free", "login_per_min")
    if not allowed:
        logger.warning("Verification rate limit exceeded for IP %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification attempts. Please try again later.",
        )

    # TODO: verify SMS code against stored code
    # For MVP stub: accept any 6-digit code
    if len(login_data.code) != 6 or not login_data.code.isdigit():
        logger.warning("Invalid verification code attempt for phone %s from IP %s", login_data.phone, client_ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    user = db.query(User).filter(User.phone == login_data.phone).first()
    if not user:
        user = User(phone=login_data.phone, phone_verified=True)
        db.add(user)
    else:
        user.phone_verified = True

    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token(str(user.id), db)
    response = TokenResponse(access_token=token, user=UserResponse.model_validate(user))
    response.refresh_token = refresh
    return response


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_access_token(
    body: RefreshRequest,
    db: Session = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token."""
    user_id = validate_refresh_token(body.refresh_token, db)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Rotate: revoke old token and issue a new access token
    revoke_refresh_token(body.refresh_token, db)
    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token(str(user.id), db)

    return RefreshResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logout: revoke the provided refresh token."""
    revoke_refresh_token(body.refresh_token, db)
    logger.info("User %s logged out", current_user.id)


@router.post("/logout/all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logout from all devices: revoke all refresh tokens for the current user."""
    count = revoke_all_user_refresh_tokens(str(current_user.id), db)
    logger.info("User %s revoked %d refresh tokens (logout all)", current_user.id, count)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user
