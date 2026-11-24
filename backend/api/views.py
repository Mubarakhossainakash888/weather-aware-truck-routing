import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services.routing import geocode_place, get_three_routes
from .services.sampling import sample_checkpoints
from .services.weather import get_checkpoint_weather_and_slider, prefetch_checkpoints_weather
from .services.risk import evaluate_risk
from .services.recommend import rank_and_recommend


@require_GET
def health(request):
    return JsonResponse({"status": "ok", "service": "weather-aware-truck-routing"})


@require_GET
def geocode(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"error": "Query parameter 'q' is required."}, status=400)
    try:
        location = geocode_place(query)
        return JsonResponse(location)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


@csrf_exempt
@require_POST
def plan_trip(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    origin_str = str(payload.get("origin", "")).strip()
    dest_str = str(payload.get("destination", "")).strip()
    departure_str = str(payload.get("departure", "")).strip()

    try:
        load_lb = float(payload.get("load_lb", 20000))
        interval_mi = int(payload.get("interval_mi", 25))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid load weight or sampling interval."}, status=400)

    if not origin_str or not dest_str:
        return JsonResponse({"error": "Origin and destination are required."}, status=400)

    try:
        departure_dt = datetime.fromisoformat(departure_str) if departure_str else datetime.now()
    except ValueError:
        return JsonResponse({"error": "Invalid departure date/time format."}, status=400)

    try:
        origin = geocode_place(origin_str)
        destination = geocode_place(dest_str)
        raw_routes = get_three_routes(origin, destination)

        sampled_list = []
        all_coords = []
        for raw in raw_routes:
            sampled = sample_checkpoints(
                coordinates=raw["coordinates"],
                total_distance_meters=raw["distance_meters"],
                total_duration_seconds=raw["duration_seconds"],
                departure_dt=departure_dt,
                interval_miles=interval_mi,
            )
            sampled_list.append(sampled)
            for cp in sampled["checkpoints"]:
                all_coords.append((cp["lat"], cp["lon"]))

        weather_source = prefetch_checkpoints_weather(all_coords)

        enriched_routes = []
        for raw, sampled in zip(raw_routes, sampled_list):
            enriched_cps = []
            for cp in sampled["checkpoints"]:
                wx = get_checkpoint_weather_and_slider(cp["lat"], cp["lon"], cp["eta_dt"])
                risk = evaluate_risk(wx["wind_mph"], wx["rain_in"], wx["snow_in"], load_lb)

                slider_points = []
                for step in wx["slider_series"]:
                    step_risk = evaluate_risk(step["wind_mph"], step["rain_in"], step["snow_in"], load_lb)
                    slider_points.append({
                        "offset": step["offset"],
                        "wind_mph": step["wind_mph"],
                        "rain_in": step["rain_in"],
                        "snow_in": step["snow_in"],
                        "risk_level": step_risk["level"],
                        "risk_score": step_risk["score"],
                    })

                enriched_cps.append({
                    "index": cp["index"],
                    "lat": cp["lat"],
                    "lon": cp["lon"],
                    "distance_miles": cp["distance_miles"],
                    "miles_covered": cp["miles_covered"],
                    "eta": cp["eta"],
                    "eta_short": cp["eta_short"],
                    "weather": {
                        "wind_mph": wx["wind_mph"],
                        "rain_in": wx["rain_in"],
                        "snow_in": wx["snow_in"],
                    },
                    "risk": risk,
                    "slider": slider_points,
                })

            enriched_routes.append({
                "id": raw["id"],
                "name": raw["name"],
                "source": raw["source"],
                "distance_miles": sampled["total_distance_miles"],
                "duration_seconds": sampled["total_duration_seconds"],
                "coordinates": raw["coordinates"],
                "checkpoints": enriched_cps,
            })

        ranked_routes = rank_and_recommend(enriched_routes)

        return JsonResponse({
            "origin": origin,
            "destination": destination,
            "departure": departure_dt.strftime("%Y-%m-%dT%H:%M"),
            "load_lb": load_lb,
            "interval_mi": interval_mi,
            "weather_source": weather_source,
            "routes": ranked_routes,
        })

    except Exception:
        return JsonResponse({"error": "Route planning failed. Please try again."}, status=400)