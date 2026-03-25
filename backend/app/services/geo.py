"""Geolocation service — distance calculation and nearby search."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta


def get_nearby_messages(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: int = 100,
    limit: int = 50,
) -> List:
    """
    Fetch messages posted within the given radius of the specified coordinates.

    Uses PostGIS ST_DWithin for efficient spatial filtering.
    Messages are ordered by creation time (newest first).
    """
    from app.models.message import Message

    # PostGIS query: filter messages within radius using geography type
    query = (
        db.query(Message)
        .filter(
            text(
                "ST_DWithin(location, ST_MakePoint(:lng, :lat)::geography, :radius)"
            ).bindparams(lat=latitude, lng=longitude, radius=radius_meters)
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return query.all()


def get_nearby_user_count(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: int = 100,
    active_within_minutes: int = 5,
) -> int:
    """
    Count active users within the given radius of the specified coordinates.

    Only counts users who updated their location within the last `active_within_minutes`.
    """
    from app.models.user import User

    cutoff_time = datetime.utcnow() - timedelta(minutes=active_within_minutes)

    count = (
        db.query(User)
        .filter(
            User.location.isnot(None),
            User.location_updated_at >= cutoff_time,
            text(
                "ST_DWithin(location, ST_MakePoint(:lng, :lat)::geography, :radius)"
            ).bindparams(lat=latitude, lng=longitude, radius=radius_meters),
        )
        .count()
    )
    return count


def calculate_distance_meters(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """
    Calculate the great-circle distance in meters between two geographic points.

    Uses the Haversine formula. Suitable for short distances.
    """
    import math

    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
