"""Event management endpoints."""

from datetime import date as date_type
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Event, Trip, TripMember
from app.routers.auth import get_current_user
from app.schemas import EventCreate, EventRead, EventUpdate

router = APIRouter(tags=["events"])


def _get_trip(db: Session, trip_id: int) -> Trip:
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def _user_role_for_trip(trip: Trip, user_id: int) -> Optional[str]:
    if trip.owner_id == user_id:
        return "owner"
    membership = next((m for m in trip.members if m.user_id == user_id), None)
    return membership.role if membership else None


def _require_view_access(trip: Trip, user_id: int) -> str:
    role = _user_role_for_trip(trip, user_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this trip")
    return role


def _require_edit_access(trip: Trip, user_id: int) -> None:
    role = _require_view_access(trip, user_id)
    if role not in {"owner", "editor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner or editor can modify events")


@router.get("/trips/{trip_id}/events", response_model=List[EventRead])
def list_events(
    trip_id: int,
    date: Optional[date_type] = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trip = _get_trip(db, trip_id)
    _require_view_access(trip, current_user.id)

    query = db.query(Event).filter(Event.trip_id == trip_id)
    if date:
        query = query.filter(Event.date == date)
    events = query.order_by(Event.date, Event.start_time).all()
    return events


@router.post("/trips/{trip_id}/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    trip_id: int,
    payload: EventCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trip = _get_trip(db, trip_id)
    _require_edit_access(trip, current_user.id)

    if payload.trip_id != trip_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip ID mismatch")

    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _get_event_or_404(db: Session, event_id: int) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    event = _get_event_or_404(db, event_id)
    trip = _get_trip(db, event.trip_id)
    _require_edit_access(trip, current_user.id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return event


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    event = _get_event_or_404(db, event_id)
    trip = _get_trip(db, event.trip_id)
    _require_edit_access(trip, current_user.id)

    db.delete(event)
    db.commit()
    return None
