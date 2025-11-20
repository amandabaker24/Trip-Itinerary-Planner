"""Trip destinations and locations management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import Trip, TripDestination, Location
from app.routers.auth import get_current_user
from app.schemas import LocationCreate, LocationRead, TripDestinationRead

router = APIRouter(prefix="/trips", tags=["destinations"])


def _get_trip(db: Session, trip_id: int) -> Trip:
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def _require_owner_or_member(trip: Trip, user_id: int) -> None:
    if trip.owner_id == user_id:
        return
    if any(m.user_id == user_id for m in trip.members):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this trip")


def _require_owner_or_editor(trip: Trip, user_id: int) -> None:
    if trip.owner_id == user_id:
        return
    member = next((m for m in trip.members if m.user_id == user_id), None)
    if member and member.role in {"owner", "editor"}:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners or editors can modify destinations")


@router.get("/{trip_id}/destinations")
def list_destinations(trip_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = _get_trip(db, trip_id)
    _require_owner_or_member(trip, current_user.id)
    destinations = (
        db.query(TripDestination)
        .options(joinedload(TripDestination.location))
        .filter(TripDestination.trip_id == trip_id)
        .order_by(TripDestination.sort_order)
        .all()
    )
    return [
        {
            "id": dest.id,
            "sort_order": dest.sort_order,
            "trip_id": dest.trip_id,
            "location": LocationRead.model_validate(dest.location),
        }
        for dest in destinations
    ]


@router.post("/{trip_id}/destinations", status_code=status.HTTP_201_CREATED)
def add_destination(
    trip_id: int,
    payload: LocationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trip = _get_trip(db, trip_id)
    _require_owner_or_editor(trip, current_user.id)

    location = Location(name=payload.name, type=payload.type, address=payload.address)
    db.add(location)
    db.commit()
    db.refresh(location)

    max_order = db.query(func.coalesce(func.max(TripDestination.sort_order), 0)).filter(TripDestination.trip_id == trip_id).scalar()
    dest = TripDestination(trip_id=trip_id, location_id=location.id, sort_order=max_order + 1)
    db.add(dest)
    db.commit()
    db.refresh(dest)

    return {"destination": TripDestinationRead.model_validate(dest), "location": LocationRead.model_validate(location)}


@router.patch("/{trip_id}/destinations/{dest_id}")
def reorder_destination(
    trip_id: int,
    dest_id: int,
    direction: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trip = _get_trip(db, trip_id)
    _require_owner_or_editor(trip, current_user.id)

    dest = db.query(TripDestination).filter(TripDestination.id == dest_id, TripDestination.trip_id == trip_id).first()
    if not dest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")

    if direction not in {"up", "down"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Direction must be 'up' or 'down'")

    if direction == "up":
        swap = (
            db.query(TripDestination)
            .filter(TripDestination.trip_id == trip_id, TripDestination.sort_order < dest.sort_order)
            .order_by(TripDestination.sort_order.desc())
            .first()
        )
    else:
        swap = (
            db.query(TripDestination)
            .filter(TripDestination.trip_id == trip_id, TripDestination.sort_order > dest.sort_order)
            .order_by(TripDestination.sort_order)
            .first()
        )

    if swap:
        dest.sort_order, swap.sort_order = swap.sort_order, dest.sort_order
        db.commit()

    return {"status": "ok"}


@router.delete("/{trip_id}/destinations/{dest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_destination(trip_id: int, dest_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = _get_trip(db, trip_id)
    _require_owner_or_editor(trip, current_user.id)

    dest = db.query(TripDestination).filter(TripDestination.id == dest_id, TripDestination.trip_id == trip_id).first()
    if not dest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")
    db.delete(dest)
    db.commit()
    return None
