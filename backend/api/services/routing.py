import os
import math
import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"


def geocode_place(query: str) -> dict:
    query = query.strip()
    if "," in query:
        parts = [p.strip() for p in query.split(",")]
        if len(parts) == 2:
            try:
                lat, lon = float(parts[0]), float(parts[1])
                return {"name": f"{lat:.4f}, {lon:.4f}", "lat": lat, "lon": lon}
            except ValueError:
                pass

    headers = {"User-Agent": "SpotterWeatherTruckRouting/1.0 (assessment-app)"}
    params = {"q": query, "format": "json", "limit": 1}
    # One retry for transient Nominatim failures (rate limit / 5xx).
    resp = None
    last_error = None
    for _attempt in range(2):
        try:
            resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            last_error = exc
            resp = None
            time.sleep(1)
    if resp is None:
        raise last_error
    results = resp.json()
    if not results:
        raise ValueError(f"Location not found: {query}")

    top = results[0]
    return {
        "name": top.get("display_name", query),
        "lat": float(top["lat"]),
        "lon": float(top["lon"]),
    }


def _fetch_ors_routes(origin: dict, destination: dict, alternatives: bool = True) -> list:
    # Strip ALL whitespace: a pasted key once carried an embedded newline
    # (with DEBUG=True) into a single env var, which broke every ORS call.
    api_key = "".join(os.environ.get("ORS_API_KEY", "").split())
    if not api_key:
        return []

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }
    body = {
        "coordinates": [
            [origin["lon"], origin["lat"]],
            [destination["lon"], destination["lat"]],
        ]
    }
    if alternatives:
        body["alternative_routes"] = {
            "target_count": 3,
            "weight_factor": 1.4,
            "share_factor": 0.6,
        }

    resp = requests.post(ORS_DIRECTIONS_URL, json=body, headers=headers, timeout=20)
    if resp.status_code != 200:
        return []

    data = resp.json()
    routes = []
    for idx, feature in enumerate(data.get("features", [])):
        summary = feature.get("properties", {}).get("summary", {})
        coords = feature.get("geometry", {}).get("coordinates", [])
        if coords and summary.get("distance"):
            routes.append({
                "id": f"ors-{idx + 1}",
                "name": f"Route {idx + 1} (Truck HGV)",
                "source": "OpenRouteService",
                "distance_meters": float(summary["distance"]),
                "duration_seconds": float(summary["duration"]),
                "coordinates": coords,
            })
    return routes


def _fetch_osrm_routes(origin: dict, destination: dict, via: dict | None = None) -> list:
    if via:
        coord_str = f"{origin['lon']},{origin['lat']};{via['lon']},{via['lat']};{destination['lon']},{destination['lat']}"
        params = {"overview": "full", "geometries": "geojson"}
    else:
        coord_str = f"{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}"
        params = {"overview": "full", "geometries": "geojson", "alternatives": "3"}

    resp = requests.get(f"{OSRM_ROUTE_URL}/{coord_str}", params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    routes = []
    for idx, r in enumerate(data.get("routes", [])):
        coords = r.get("geometry", {}).get("coordinates", [])
        if coords and r.get("distance"):
            routes.append({
                "id": f"osrm-{idx + 1}",
                "name": f"Route {idx + 1}",
                "source": "OSRM",
                "distance_meters": float(r["distance"]),
                "duration_seconds": float(r["duration"]),
                "coordinates": coords,
            })
    return routes


def _is_distinct_route(candidate: dict, existing: list) -> bool:
    for r in existing:
        dist_diff = abs(candidate["distance_meters"] - r["distance_meters"])
        dur_diff = abs(candidate["duration_seconds"] - r["duration_seconds"])
        if dist_diff < 1500 and dur_diff < 120:
            return False
    return True


def get_three_routes(origin: dict, destination: dict) -> list:
    routes = []

    # 1. Try OpenRouteService with 3 alternative truck routes
    ors_alt = _fetch_ors_routes(origin, destination, alternatives=True)
    for r in ors_alt:
        if _is_distinct_route(r, routes):
            routes.append(r)

    # 2. If ORS alternatives failed (e.g., long haul >100km), fetch primary ORS truck route
    if not routes:
        ors_single = _fetch_ors_routes(origin, destination, alternatives=False)
        for r in ors_single:
            if _is_distinct_route(r, routes):
                routes.append(r)

    # 3. Fill remaining slots up to 3 using OSRM alternatives
    if len(routes) < 3:
        try:
            osrm_routes = _fetch_osrm_routes(origin, destination)
            for r in osrm_routes:
                if _is_distinct_route(r, routes) and len(routes) < 3:
                    routes.append(r)
        except Exception:
            pass

    # 4. If still fewer than 3 routes exist, generate slight corridor detour options
    if len(routes) < 3:
        mid_lat = (origin["lat"] + destination["lat"]) / 2
        mid_lon = (origin["lon"] + destination["lon"]) / 2
        dlat = destination["lat"] - origin["lat"]
        dlon = destination["lon"] - origin["lon"]
        length = math.hypot(dlat, dlon) or 1.0
        perp_lat = -dlon / length
        perp_lon = dlat / length

        for factor in (0.18, -0.18, 0.30, -0.30):
            if len(routes) >= 3:
                break
            via = {
                "lat": mid_lat + perp_lat * length * factor,
                "lon": mid_lon + perp_lon * length * factor,
            }
            try:
                detour = _fetch_osrm_routes(origin, destination, via=via)
                for r in detour:
                    if _is_distinct_route(r, routes) and len(routes) < 3:
                        routes.append(r)
            except Exception:
                continue

    if not routes:
        raise ValueError("Could not find any driving route between these locations.")

    for idx, r in enumerate(routes[:3]):
        r["id"] = f"route-{idx + 1}"
        r["name"] = f"Route {idx + 1}"

    return routes[:3]