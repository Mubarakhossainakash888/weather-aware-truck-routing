import math
from datetime import datetime, timedelta

EARTH_RADIUS_MILES = 3958.7613
METERS_PER_MILE = 1609.344


def haversine_miles(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def sample_checkpoints(
    coordinates: list,
    total_distance_meters: float,
    total_duration_seconds: float,
    departure_dt: datetime,
    interval_miles: int = 25,
) -> dict:
    total_distance_miles = total_distance_meters / METERS_PER_MILE
    if interval_miles not in (10, 25, 50):
        interval_miles = 25

    # Compute cumulative polyline distances
    cum_dists = [0.0]
    for i in range(1, len(coordinates)):
        lon1, lat1 = coordinates[i - 1]
        lon2, lat2 = coordinates[i]
        seg = haversine_miles(lon1, lat1, lon2, lat2)
        cum_dists.append(cum_dists[-1] + seg)

    poly_total = cum_dists[-1] if cum_dists[-1] > 0 else total_distance_miles
    scale = (total_distance_miles / poly_total) if poly_total > 0 else 1.0

    # Target sample distances: 0, interval, 2*interval, ...
    target_distances = [0.0]
    current = float(interval_miles)
    while current < total_distance_miles - 0.5:
        target_distances.append(current)
        current += interval_miles

    checkpoints = []
    seg_idx = 0

    for idx, target_mi in enumerate(target_distances):
        poly_target = target_mi / scale if scale > 0 else target_mi

        while seg_idx < len(cum_dists) - 2 and cum_dists[seg_idx + 1] < poly_target:
            seg_idx += 1

        d0 = cum_dists[seg_idx]
        d1 = cum_dists[seg_idx + 1] if seg_idx + 1 < len(cum_dists) else d0
        lon0, lat0 = coordinates[seg_idx]
        lon1, lat1 = coordinates[seg_idx + 1] if seg_idx + 1 < len(coordinates) else coordinates[seg_idx]

        if d1 > d0:
            t = max(0.0, min(1.0, (poly_target - d0) / (d1 - d0)))
        else:
            t = 0.0

        lon = lon0 + t * (lon1 - lon0)
        lat = lat0 + t * (lat1 - lat0)

        next_mi = target_distances[idx + 1] if idx + 1 < len(target_distances) else total_distance_miles
        miles_covered = max(0.0, next_mi - target_mi)

        ratio = (target_mi / total_distance_miles) if total_distance_miles > 0 else 0.0
        eta_dt = departure_dt + timedelta(seconds=total_duration_seconds * ratio)

        checkpoints.append({
            "index": idx + 1,
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "distance_miles": round(target_mi, 1),
            "miles_covered": round(miles_covered, 2),
            "elapsed_seconds": round(total_duration_seconds * ratio),
            "eta_dt": eta_dt,
            "eta": eta_dt.strftime("%Y-%m-%d %H:%M"),
            "eta_short": eta_dt.strftime("%b %d, %I:%M %p"),
        })

    return {
        "total_distance_miles": round(total_distance_miles, 1),
        "total_duration_seconds": round(total_duration_seconds),
        "checkpoints": checkpoints,
    }