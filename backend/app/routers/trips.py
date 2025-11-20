"""Trip management endpoints."""

from typing import List, Optional
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.db import get_db
from app.models import Trip, TripMember, Event, BudgetEnvelope, Expense, WeatherAlert
from app.routers.auth import get_current_user
from app.schemas import (
    TripCreate,
    TripMemberRead,
    TripRead,
    TripUpdate,
)

router = APIRouter(prefix="/trips", tags=["trips"])


class TripMemberUpsert(BaseModel):
    user_id: int
    role: str


def _get_trip_or_404(db: Session, trip_id: int) -> Trip:
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def _ensure_member_or_owner(trip: Trip, user_id: int) -> None:
    is_owner = trip.owner_id == user_id
    is_member = any(member.user_id == user_id for member in trip.members)
    if not (is_owner or is_member):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this trip")


def _ensure_owner(trip: Trip, user_id: int) -> None:
    if trip.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can perform this action")


@router.get("", response_model=List[TripRead])
def list_trips(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trips = (
        db.query(Trip)
        .outerjoin(TripMember, TripMember.trip_id == Trip.id)
        .filter(or_(Trip.owner_id == current_user.id, TripMember.user_id == current_user.id))
        .distinct()
        .all()
    )
    return trips


@router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(payload: TripCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip_data = payload.model_dump(exclude={"owner_id"})
    trip = Trip(owner_id=current_user.id, **trip_data)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@router.get("/{trip_id}", response_model=TripRead)
def get_trip(trip_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = _get_trip_or_404(db, trip_id)
    _ensure_member_or_owner(trip, current_user.id)
    return trip


@router.patch("/{trip_id}", response_model=TripRead)
def update_trip(
    trip_id: int,
    payload: TripUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trip = _get_trip_or_404(db, trip_id)
    _ensure_owner(trip, current_user.id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)

    db.commit()
    db.refresh(trip)
    return trip


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = _get_trip_or_404(db, trip_id)
    _ensure_owner(trip, current_user.id)

    db.delete(trip)
    db.commit()
    return None


@router.get("/{trip_id}/members", response_model=List[TripMemberRead])
def list_trip_members(trip_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = _get_trip_or_404(db, trip_id)
    _ensure_member_or_owner(trip, current_user.id)
    return trip.members


@router.post("/{trip_id}/members", response_model=TripMemberRead, status_code=status.HTTP_201_CREATED)
def add_or_update_member(
    trip_id: int,
    payload: TripMemberUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trip = _get_trip_or_404(db, trip_id)
    _ensure_owner(trip, current_user.id)

    member = (
        db.query(TripMember)
        .filter(TripMember.trip_id == trip_id, TripMember.user_id == payload.user_id)
        .first()
    )
    if member:
        member.role = payload.role
    else:
        member = TripMember(trip_id=trip_id, user_id=payload.user_id, role=payload.role)
        db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{trip_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    trip_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trip = _get_trip_or_404(db, trip_id)
    _ensure_owner(trip, current_user.id)

    member = (
        db.query(TripMember)
        .filter(TripMember.trip_id == trip_id, TripMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    db.delete(member)
    db.commit()
    return None


@router.get("/{trip_id}/export/pdf")
def export_trip_pdf(trip_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = _get_trip_or_404(db, trip_id)
    _ensure_member_or_owner(trip, current_user.id)

    events = (
        db.query(Event)
        .filter(Event.trip_id == trip_id)
        .order_by(Event.date, Event.start_time)
        .all()
    )
    envelopes = db.query(BudgetEnvelope).filter(BudgetEnvelope.trip_id == trip_id).all()
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    alerts = db.query(WeatherAlert).filter(WeatherAlert.trip_id == trip_id).all()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"Trip: {trip.name}")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Destination: {trip.destination}")
    y -= 15
    p.drawString(50, y, f"Dates: {trip.start_date} to {trip.end_date}")
    y -= 25

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Events")
    y -= 18
    p.setFont("Helvetica", 11)
    for evt in events:
        line = f"{evt.date} - {evt.title} ({evt.type})"
        if evt.start_time:
            line += f" @ {evt.start_time}"
        p.drawString(60, y, line)
        y -= 14
        if y < 80:
            p.showPage()
            y = height - 50

    y -= 10
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Budget")
    y -= 18
    p.setFont("Helvetica", 11)
    for env in envelopes:
        actual = sum(exp.amount for exp in expenses if exp.envelope_id == env.id)
        p.drawString(60, y, f"{env.category}: planned ${env.planned_amount:.2f} / actual ${actual:.2f}")
        y -= 14
        if y < 80:
            p.showPage()
            y = height - 50

    if alerts:
        y -= 10
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Weather Alerts")
        y -= 18
        p.setFont("Helvetica", 11)
        for alert in alerts:
            p.drawString(60, y, f"{alert.date} [{alert.severity}] {alert.summary}")
            y -= 14
            if y < 80:
                p.showPage()
                y = height - 50

    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="trip-{trip_id}.pdf"'})
