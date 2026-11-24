import math
import time
import requests
from datetime import datetime, timedelta, timezone

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_WEATHER_CACHE = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes


def _to_utc_naive(dt_val) -> datetime:
    if isinstance(dt_val, str):
        cleaned = dt_val.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
    else:
        dt = dt_val
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _build_synthetic_hourly(lat: float, lon: float, base_dt: datetime) -> dict:
    times = []
    winds = []
    rains = []
    snows = []

    start_dt = base_dt.replace(minute=0, second=0, microsecond=0) - timedelta(hours=2)
    northern_factor = max(0.0, (lat - 38.0) / 8.0)

    for h in range(120):
        t = start_dt + timedelta(hours=h)
        times.append(t.isoformat())

        wave = math.sin((h / 6.0) + (lat * 0.7) + (lon * 0.3))
        gust = math.cos((h / 4.0) - (lon * 0.5))
        storm_spike = max(0.0, math.sin((h / 8.0) + (lon * 0.4)) - 0.55) * 38.0

        wind = max(6.0, round(15.0 + (wave * 11.0) + (gust * 7.0) + (northern_factor * 5.0) + storm_spike, 1))
        precip_signal = max(0.0, wave + (gust * 0.65) - 0.45)

        if lat >= 40.5 and (h % 24 in range(0, 12) or lat >= 42.5):
            snow = round(precip_signal * 0.95 * (1.0 + northern_factor), 2)
            rain = 0.0
        else:
            rain = round(precip_signal * 0.42, 2)
            snow = 0.0

        winds.append(wind)
        rains.append(rain)
        snows.append(snow)

    return {
        "time": times,
        "wind_speed_10m": winds,
        "rain": rains,
        "snowfall": snows,
    }


def _extract_at_time(hourly: dict, target_dt: datetime) -> dict:
    times = hourly.get("time", [])
    winds = hourly.get("wind_speed_10m", [])
    rains = hourly.get("rain", [])
    snows = hourly.get("snowfall", [])

    if not times:
        return {"wind_mph": 0.0, "rain_in": 0.0, "snow_in": 0.0}

    best_idx = 0
    best_diff = float("inf")
    for idx, t_str in enumerate(times):
        t_dt = _to_utc_naive(t_str)
        diff = abs((t_dt - target_dt).total_seconds())
        if diff < best_diff:
            best_diff = diff
            best_idx = idx

    return {
        "wind_mph": round(float(winds[best_idx] or 0.0), 1),
        "rain_in": round(float(rains[best_idx] or 0.0), 2),
        "snow_in": round(float(snows[best_idx] or 0.0), 2),
    }


def prefetch_checkpoints_weather(points: list[tuple[float, float]]) -> str:
    if not points:
        return "live"

    now = time.time()
    unique_missing = []
    seen = set()
    sources_used = set()

    for lat, lon in points:
        key = (round(float(lat), 1), round(float(lon), 1))
        if key in seen:
            continue
        seen.add(key)
        cached = _WEATHER_CACHE.get(key)
        if cached and (now - cached["ts"]) < CACHE_TTL_SECONDS:
            sources_used.add(cached.get("source", "live"))
        else:
            unique_missing.append(key)

    if not unique_missing:
        return "simulated" if "simulated" in sources_used else "live"

    lats = ",".join(str(p[0]) for p in unique_missing)
    lons = ",".join(str(p[1]) for p in unique_missing)

    params = {
        "latitude": lats,
        "longitude": lons,
        "hourly": "wind_speed_10m,rain,snowfall",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": 5,
        "timezone": "UTC",
    }
    headers = {
        "User-Agent": "SpotterWeatherTruckRouting/1.0 (contact@spotter-routing.app)"
    }

    for attempt in range(3):
        try:
            resp = requests.get(OPEN_METEO_URL, params=params, headers=headers, timeout=12)
            if resp.status_code == 200:
                payload = resp.json()
                items = payload if isinstance(payload, list) else [payload]
                for key, item in zip(unique_missing, items):
                    _WEATHER_CACHE[key] = {
                        "ts": time.time(),
                        "source": "live",
                        "hourly": item.get("hourly", {}),
                    }
                return "simulated" if "simulated" in sources_used else "live"
            if resp.status_code == 429 and attempt < 2:
                retry_after = resp.headers.get("Retry-After")
                wait_sec = min(float(retry_after), 4.0) if retry_after and retry_after.isdigit() else (1.5 * (attempt + 1))
                time.sleep(wait_sec)
                continue
            break
        except Exception:
            if attempt < 2:
                time.sleep(1.0)
                continue
            break

    now_dt = datetime.now(timezone.utc).replace(tzinfo=None)
    for key in unique_missing:
        _WEATHER_CACHE[key] = {
            "ts": time.time(),
            "source": "simulated",
            "hourly": _build_synthetic_hourly(key[0], key[1], now_dt),
        }
    return "simulated"


def get_checkpoint_weather_and_slider(lat: float, lon: float, eta_dt) -> dict:
    key = (round(float(lat), 1), round(float(lon), 1))
    cached = _WEATHER_CACHE.get(key)
    if not cached or (time.time() - cached["ts"]) >= CACHE_TTL_SECONDS:
        prefetch_checkpoints_weather([key])
        cached = _WEATHER_CACHE.get(key, {"hourly": {}, "source": "live"})

    hourly = cached["hourly"]
    base_dt = _to_utc_naive(eta_dt)
    current_wx = _extract_at_time(hourly, base_dt)

    slider_series = []
    for offset in range(0, 49, 1):
        step_dt = base_dt + timedelta(hours=offset)
        step_wx = _extract_at_time(hourly, step_dt)
        slider_series.append({
            "offset": offset,
            "wind_mph": step_wx["wind_mph"],
            "rain_in": step_wx["rain_in"],
            "snow_in": step_wx["snow_in"],
        })

    return {
        "wind_mph": current_wx["wind_mph"],
        "rain_in": current_wx["rain_in"],
        "snow_in": current_wx["snow_in"],
        "source": cached.get("source", "live"),
        "slider_series": slider_series,
    }