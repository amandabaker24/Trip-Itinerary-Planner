from datetime import date
from typing import Dict, List, Optional, Tuple

import httpx


async def geocode_city(name: str) -> Optional[Tuple[float, float]]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": name, "count": 1}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results") or []
            if not results:
                return None
            first = results[0]
            return float(first["latitude"]), float(first["longitude"])
        except Exception:
            return None


async def fetch_daily_forecast(lat: float, lon: float, start_date: date, end_date: date) -> List[Dict]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            daily = resp.json().get("daily", {})
        except Exception:
            return []

    dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_probability_max", [])

    results: List[Dict] = []
    for idx, d in enumerate(dates):
        prob = precip[idx] if idx < len(precip) else 0
        hi = tmax[idx] if idx < len(tmax) else None
        lo = tmin[idx] if idx < len(tmin) else None
        summary = "Clear"
        advice = "Good weather – great day for walking and outdoor plans."
        if prob >= 70:
            summary = "Rainy"
            advice = "Heavy rain expected – plan indoor activities or rideshares."
        elif prob >= 40:
            summary = "Cloudy"
            advice = "Chance of showers – keep an umbrella handy and have a backup indoor option."
        if hi is not None and hi >= 32:
            advice = "Very hot – schedule outdoor activities early and stay hydrated."
        if lo is not None and lo <= 35:
            advice = "Cold weather – bring layers and keep walks shorter."

        results.append(
            {
                "date": date.fromisoformat(d),
                "temp_max": hi if hi is not None else 0.0,
                "temp_min": lo if lo is not None else 0.0,
                "precip_prob": int(prob),
                "summary": summary,
                "advice": advice,
            }
        )
    return results
