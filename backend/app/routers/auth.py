"""Authentication router — register, login, verify endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.services.auth import create_access_token, get_current_user

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
        return TokenResponse(access_token=token, user=UserResponse.model_validate(existing))

    # Create new guest user
    user = User(device_id=user_data.device_id)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


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
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user
