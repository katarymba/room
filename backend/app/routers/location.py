"""Location router — update user location endpoint."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.schemas.user import LocationUpdate, UserResponse
from app.services.auth import get_current_user

router = APIRouter()


@router.put("/", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_location(
    location_data: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's location. Called periodically by the mobile app."""
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point

    point = from_shape(Point(location_data.longitude, location_data.latitude), srid=4326)
    current_user.location = point
    current_user.location_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)
    return current_user
