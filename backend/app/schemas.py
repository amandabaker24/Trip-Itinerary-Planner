"""Pydantic schemas for request/response models."""

from datetime import date, time
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserLogin(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class UserRead(BaseModel):
    id: int
    email: str
    username: str

    model_config = ConfigDict(from_attributes=True)


class TripCreate(BaseModel):
    owner_id: Optional[int] = None
    name: str
    destination: str
    start_date: date
    end_date: date


class TripUpdate(BaseModel):
    name: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TripRead(BaseModel):
    id: int
    owner_id: int
    name: str
    destination: str
    start_date: date
    end_date: date

    model_config = ConfigDict(from_attributes=True)


class TripMemberRead(BaseModel):
    id: int
    trip_id: int
    user_id: int
    role: str

    model_config = ConfigDict(from_attributes=True)


class LocationCreate(BaseModel):
    name: str
    type: str
    address: Optional[str] = None


class LocationRead(BaseModel):
    id: int
    name: str
    type: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class TripDestinationCreate(BaseModel):
    trip_id: int
    location_id: int
    sort_order: Optional[int] = 0


class TripDestinationRead(BaseModel):
    id: int
    trip_id: int
    location_id: int
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class EventCreate(BaseModel):
    trip_id: int
    location_id: Optional[int] = None
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    title: str
    type: str
    cost: Optional[float] = None
    notes: Optional[str] = None


class EventUpdate(BaseModel):
    location_id: Optional[int] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    title: Optional[str] = None
    type: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None


class EventRead(BaseModel):
    id: int
    trip_id: int
    location_id: Optional[int] = None
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    title: str
    type: str
    cost: Optional[float] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BudgetEnvelopeCreate(BaseModel):
    trip_id: int
    category: str
    planned_amount: float
    notes: Optional[str] = None


class BudgetEnvelopeRead(BaseModel):
    id: int
    trip_id: int
    category: str
    planned_amount: float
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExpenseCreate(BaseModel):
    trip_id: int
    envelope_id: Optional[int] = None
    event_id: Optional[int] = None
    description: str
    amount: float
    currency: str = "USD"
    spent_at_date: date


class ExpenseRead(BaseModel):
    id: int
    trip_id: int
    envelope_id: Optional[int] = None
    event_id: Optional[int] = None
    description: str
    amount: float
    currency: str
    spent_at_date: date

    model_config = ConfigDict(from_attributes=True)


class WeatherAlertRead(BaseModel):
    id: int
    trip_id: int
    date: date
    severity: str
    summary: str
    provider_payload: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class TripWeatherDay(BaseModel):
    date: date
    temp_max: float
    temp_min: float
    precip_prob: int
    summary: str
    advice: str

    class Config:
        orm_mode = False


class TripWeatherResponse(BaseModel):
    city: str
    start_date: date
    end_date: date
    days: list[TripWeatherDay]
