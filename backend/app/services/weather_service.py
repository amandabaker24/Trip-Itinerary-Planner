from datetime import date
from typing import Dict, List

import httpx
from sqlalchemy.orm import Session

from app.models import Location, Trip, TripDestination, WeatherAlert


async def fetch_daily_weather(lat: float, lon: float, start_date: date, end_date: date) -> Dict[date, dict]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": ["precipitation_sum", "precipitation_probability_max", "windspeed_10m_max", "temperature_2m_max"],
        "timezone": "UTC",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json().get("daily", {})

    dates = data.get("time", [])
    precip = data.get("precipitation_sum", [])
    precip_prob = data.get("precipitation_probability_max", [])
    wind = data.get("windspeed_10m_max", [])

    result: Dict[date, dict] = {}
    for idx, d in enumerate(dates):
        summary = "clear"
        severity = "low"
        p = precip[idx] if idx < len(precip) else 0
        prob = precip_prob[idx] if idx < len(precip_prob) else 0
        w = wind[idx] if idx < len(wind) else 0

        if prob >= 70 or p >= 10 or w >= 40:
            summary = "heavy rain / strong wind"
            severity = "high"
        elif prob >= 40 or p >= 5 or w >= 25:
            summary = "rainy / breezy"
            severity = "medium"
        else:
            summary = "looks clear"
            severity = "low"

        result[date.fromisoformat(d)] = {
            "summary": summary,
            "severity": severity,
            "raw": {
                "precip": p,
                "precip_prob": prob,
                "wind": w,
            },
        }
    return result


def _primary_location_for_trip(trip: Trip) -> Location | None:
    if trip.destinations:
        return trip.destinations[0].location
    return None


async def build_weather_alerts_for_trip(trip: Trip, db: Session) -> List[WeatherAlert]:
    location = _primary_location_for_trip(trip)
    if not location or location.latitude is None or location.longitude is None:
        return []

    daily = await fetch_daily_weather(location.latitude, location.longitude, trip.start_date, trip.end_date)
    alerts: List[WeatherAlert] = []
    for d, info in daily.items():
        severity = info["severity"]
        if severity == "low":
            continue
        alert = (
            db.query(WeatherAlert)
            .filter(WeatherAlert.trip_id == trip.id, WeatherAlert.date == d)
            .first()
        )
        if not alert:
            alert = WeatherAlert(trip_id=trip.id, date=d, severity=severity, summary=info["summary"], provider_payload=info["raw"])
            db.add(alert)
        else:
            alert.severity = severity
            alert.summary = info["summary"]
            alert.provider_payload = info["raw"]
        alerts.append(alert)
    db.commit()
    return alerts
