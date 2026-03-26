"""Authentication service — JWT token generation and validation."""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with the given payload data."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_token(token: str) -> Optional[dict]:
    """Decode a JWT token and return its payload, or *None* if invalid/expired."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def create_refresh_token(user_id: str, db: Session) -> str:
    """Create a new refresh token, persist it in the DB and return the token string."""
    from app.models.refresh_token import RefreshToken

    token_value = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = RefreshToken(
        user_id=user_id,
        token=token_value,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()
    return token_value


def validate_refresh_token(token: str, db: Session) -> Optional[str]:
    """Validate a refresh token and return the associated user_id, or None if invalid/expired."""
    from app.models.refresh_token import RefreshToken

    record = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if record is None:
        return None
    if record.revoked:
        return None
    if record.expires_at < datetime.utcnow():
        return None
    return str(record.user_id)


def revoke_refresh_token(token: str, db: Session) -> bool:
    """Revoke a refresh token. Returns True if the token was found and revoked."""
    from app.models.refresh_token import RefreshToken

    record = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if record is None:
        return False
    record.revoked = True
    db.commit()
    return True


def revoke_all_user_refresh_tokens(user_id: str, db: Session) -> int:
    """Revoke all active refresh tokens for a user. Returns the count revoked."""
    from app.models.refresh_token import RefreshToken

    count = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.revoked == False)  # noqa: E712
        .update({"revoked": True})
    )
    db.commit()
    return count


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """FastAPI dependency that returns the currently authenticated user."""
    from app.models.user import User

    payload = decode_access_token(credentials.credentials)
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user
