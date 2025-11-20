"""Live weather forecast for a trip."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Trip
from app.routers.auth import get_current_user
from app.schemas import TripWeatherDay, TripWeatherResponse
from app.services.weather_client import geocode_city, fetch_daily_forecast

router = APIRouter(tags=["weather"])


def _get_trip(db: Session, trip_id: int) -> Trip:
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


def _user_role_for_trip(trip: Trip, user_id: int):
    if trip.owner_id == user_id:
        return "owner"
    membership = next((m for m in trip.members if m.user_id == user_id), None)
    return membership.role if membership else None


def _require_view_access(trip: Trip, user_id: int) -> None:
    role = _user_role_for_trip(trip, user_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not authorized for this trip")


@router.get("/trips/{trip_id}/weather", response_model=TripWeatherResponse)
async def trip_weather(trip_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = _get_trip(db, trip_id)
    _require_view_access(trip, current_user.id)

    coords = await geocode_city(trip.destination)
    if not coords:
        raise HTTPException(status_code=404, detail="Could not find location for this trip's destination")

    lat, lon = coords
    daily = await fetch_daily_forecast(lat, lon, trip.start_date, trip.end_date)
    days = [TripWeatherDay(**d) for d in daily]
    return TripWeatherResponse(city=trip.destination, start_date=trip.start_date, end_date=trip.end_date, days=days)
