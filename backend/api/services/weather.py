from datetime import datetime, timedelta
import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_WEATHER_CACHE = {}


def _fetch_hourly_grid(lat: float, lon: float) -> dict:
    key = (round(lat, 2), round(lon, 2))
    if key in _WEATHER_CACHE:
        return _WEATHER_CACHE[key]

    params = {
        "latitude": key[0],
        "longitude": key[1],
        "hourly": "wind_speed_10m,rain,snowfall",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": 4,
        "timezone": "auto",
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
    resp.raise_for_status()
    hourly = resp.json().get("hourly", {})

    times = hourly.get("time", [])
    winds = hourly.get("wind_speed_10m", [])
    rains = hourly.get("rain", [])
    snows = hourly.get("snowfall", [])

    parsed = []
    for i, t_str in enumerate(times):
        parsed.append({
            "time_str": t_str,
            "dt": datetime.fromisoformat(t_str),
            "wind_mph": round(float(winds[i] or 0.0), 1),
            "rain_in": round(float(rains[i] or 0.0), 3),
            "snow_in": round(float(snows[i] or 0.0), 3),
        })

    _WEATHER_CACHE[key] = parsed
    return parsed


def _closest_hour_entry(parsed_hours: list, target_dt: datetime) -> dict:
    if not parsed_hours:
        return {"wind_mph": 0.0, "rain_in": 0.0, "snow_in": 0.0, "time_str": target_dt.strftime("%Y-%m-%dT%H:00")}

    best = min(parsed_hours, key=lambda item: abs((item["dt"] - target_dt).total_seconds()))
    return best


def get_checkpoint_weather_and_slider(lat: float, lon: float, eta_dt: datetime) -> dict:
    parsed_hours = _fetch_hourly_grid(lat, lon)
    base_weather = _closest_hour_entry(parsed_hours, eta_dt)

    # Pre-compute 0 to 48 hour forecast offsets for instant frontend slider updates
    slider_series = []
    for offset in range(49):
        shifted_dt = eta_dt + timedelta(hours=offset)
        entry = _closest_hour_entry(parsed_hours, shifted_dt)
        slider_series.append({
            "offset": offset,
            "wind_mph": entry["wind_mph"],
            "rain_in": entry["rain_in"],
            "snow_in": entry["snow_in"],
        })

    return {
        "wind_mph": base_weather["wind_mph"],
        "rain_in": base_weather["rain_in"],
        "snow_in": base_weather["snow_in"],
        "slider_series": slider_series,
    }