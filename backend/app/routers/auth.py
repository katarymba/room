"""Authentication router — register, login, verify, refresh, logout endpoints."""
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.services.auth import (
    create_access_token,
    get_current_user,
    issue_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
)
from app.services.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register/guest", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_guest(user_data: UserCreate, db: Session = Depends(get_db)):
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
        refresh = issue_refresh_token(db, existing.id)
        return TokenResponse(
            access_token=token,
            refresh_token=refresh,
            user=UserResponse.model_validate(existing),
        )

    # Create new guest user
    user = User(device_id=user_data.device_id)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    refresh = issue_refresh_token(db, user.id)
    return TokenResponse(
        access_token=token,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/register/phone", response_model=dict, status_code=status.HTTP_200_OK)
async def request_phone_verification(user_data: UserCreate, db: Session = Depends(get_db)):
    """Request SMS verification code for phone-based authentication."""
    if not user_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="phone is required",
        )

    # In production, send SMS code via provider
    # For MVP, log the code or use a stub
    # TODO: integrate SMS provider (Twilio, etc.)
    return {"message": "Verification code sent", "phone": user_data.phone}


@router.post("/verify/phone", response_model=TokenResponse)
async def verify_phone(login_data: UserLogin, db: Session = Depends(get_db)):
    """Verify SMS code and authenticate user."""
    if not login_data.phone or not login_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="phone and code are required",
        )

    # Rate-limit login attempts by phone number
    rate_key = f"login:{login_data.phone}"
    allowed, _ = check_rate_limit(rate_key, "free", "login_per_minute")
    if not allowed:
        logger.warning("Login rate limit exceeded for phone %s", login_data.phone)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    # TODO: verify SMS code against stored code
    # For MVP stub: accept any 6-digit code
    if len(login_data.code) != 6 or not login_data.code.isdigit():
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
    refresh = issue_refresh_token(db, user.id)
    return TokenResponse(
        access_token=token,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token (token rotation).

    The old refresh token is revoked and a new one is issued.
    """
    record = verify_refresh_token(db, refresh_token)

    # Revoke the used refresh token (rotation)
    record.revoked = True
    db.commit()

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access = create_access_token({"sub": str(user.id)})
    new_refresh = issue_refresh_token(db, user.id)
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invalidate the provided refresh token (logout).

    The access token remains valid until it expires naturally (short TTL).
    Token not found or already revoked is treated as success to avoid enumeration.
    """
    revoke_refresh_token(db, refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user
