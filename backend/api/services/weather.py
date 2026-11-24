import time
import requests
from datetime import datetime, timezone

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_WEATHER_CACHE = {}
CACHE_TTL_SECONDS = 900  # 15 minutes


def _parse_iso_to_utc(dt_str: str) -> datetime:
    cleaned = dt_str.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _select_hourly_weather(hourly: dict, target_dt: datetime) -> dict:
    times = hourly.get("time", [])
    winds = hourly.get("wind_speed_10m", [])
    rains = hourly.get("rain", [])
    snows = hourly.get("snowfall", [])

    if not times:
        return {
            "wind_mph": 0.0,
            "rain_in": 0.0,
            "snow_in": 0.0,
            "forecast_time": target_dt.isoformat(),
        }

    best_idx = 0
    best_diff = float("inf")
    for idx, t_str in enumerate(times):
        t_dt = _parse_iso_to_utc(t_str)
        diff = abs((t_dt - target_dt).total_seconds())
        if diff < best_diff:
            best_diff = diff
            best_idx = idx

    return {
        "wind_mph": round(float(winds[best_idx] or 0.0), 1),
        "rain_in": round(float(rains[best_idx] or 0.0), 2),
        "snow_in": round(float(snows[best_idx] or 0.0), 2),
        "forecast_time": times[best_idx],
    }


def fetch_batch_weather(points: list[tuple[float, float]]) -> list[dict]:
    """
    Fetches hourly forecasts for multiple (lat, lon) points in a single Open-Meteo request
    with in-memory caching to avoid 429 rate limits on shared cloud IPs.
    """
    if not points:
        return []

    now = time.time()
    rounded_points = [(round(lat, 2), round(lon, 2)) for lat, lon in points]
    results = [None] * len(rounded_points)
    missing_indices = []
    missing_coords = []

    for idx, coord in enumerate(rounded_points):
        cached = _WEATHER_CACHE.get(coord)
        if cached and (now - cached["ts"]) < CACHE_TTL_SECONDS:
            results[idx] = cached["hourly"]
        else:
            missing_indices.append(idx)
            missing_coords.append(coord)

    if missing_coords:
        lats = ",".join(str(c[0]) for c in missing_coords)
        lons = ",".join(str(c[1]) for c in missing_coords)
        params = {
            "latitude": lats,
            "longitude": lons,
            "hourly": "wind_speed_10m,rain,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "forecast_days": 4,
            "timezone": "UTC",
        }

        resp = None
        for attempt in range(3):
            resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
            if resp.status_code != 429:
                break
            time.sleep(1.5 * (attempt + 1))

        resp.raise_for_status()
        payload = resp.json()

        # Open-Meteo returns a dict for 1 coordinate, or a list of dicts for multiple coordinates
        hourly_list = payload if isinstance(payload, list) else [payload]

        for idx, item in zip(missing_indices, hourly_list):
            hourly_data = item.get("hourly", {})
            _WEATHER_CACHE[rounded_points[idx]] = {
                "ts": time.time(),
                "hourly": hourly_data,
            }
            results[idx] = hourly_data

    return results


def get_weather_at_eta(lat: float, lon: float, eta_iso: str, hourly_data: dict | None = None) -> dict:
    target_dt = _parse_iso_to_utc(eta_iso)
    if hourly_data is None:
        hourly_data = fetch_batch_weather([(lat, lon)])[0]
    return _select_hourly_weather(hourly_data, target_dt)