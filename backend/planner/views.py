import os
from datetime import datetime, timezone

import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .hos_engine import Leg, simulate_trip, build_daily_logs

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = os.environ.get("OSRM_BASE_URL", "https://router.project-osrm.org")

HEADERS = {"User-Agent": "eld-trip-planner-assessment/1.0"}


def geocode(place: str):
    """Turn a free-text address into (lat, lon) using OSM Nominatim."""
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": place, "format": "json", "limit": 1},
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError(f"Could not find a location for '{place}'")
    return float(data[0]["lat"]), float(data[0]["lon"])


def osrm_route(points):
    """points: list of (lat, lon) tuples, in order. Returns geometry + per-leg distance/duration."""
    coord_str = ";".join(f"{lon},{lat}" for lat, lon in points)
    url = f"{OSRM_URL}/route/v1/driving/{coord_str}"
    resp = requests.get(
        url,
        params={"overview": "full", "geometries": "geojson", "steps": "false"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("Could not compute a route between the given locations")

    route = data["routes"][0]
    legs = route["legs"] 
    geometry = route["geometry"]  

    return geometry, legs


@api_view(["POST"])
def plan_trip(request):
    payload = request.data

    current_location = str(payload.get("current_location") or "").strip()
    pickup_location = str(payload.get("pickup_location") or "").strip()
    dropoff_location = str(payload.get("dropoff_location") or "").strip()
    cycle_used = payload.get("current_cycle_used_hours", 0)

    if not (current_location and pickup_location and dropoff_location):
        return Response(
            {"error": "current_location, pickup_location and dropoff_location are required."},
            status=400,
        )

    try:
        cycle_used = float(cycle_used)
    except (TypeError, ValueError):
        return Response({"error": "current_cycle_used_hours must be a number."}, status=400)

    if cycle_used < 0 or cycle_used > 70:
        return Response({"error": "current_cycle_used_hours must be between 0 and 70."}, status=400)

    try:
        current_pt = geocode(current_location)
        pickup_pt = geocode(pickup_location)
        dropoff_pt = geocode(dropoff_location)
    except Exception as exc: 
        return Response({"error": f"Geocoding failed: {exc}"}, status=400)

    try:
        geometry, route_legs = osrm_route([current_pt, pickup_pt, dropoff_pt])
    except Exception as exc:  
        return Response({"error": f"Routing failed: {exc}"}, status=400)

    leg1 = Leg(
        label="to_pickup",
        from_label=current_location,
        to_label=pickup_location,
        distance_miles=route_legs[0]["distance"] / 1609.34,
        duration_hours=route_legs[0]["duration"] / 3600.0,
    )
    leg2 = Leg(
        label="to_dropoff",
        from_label=pickup_location,
        to_label=dropoff_location,
        distance_miles=route_legs[1]["distance"] / 1609.34,
        duration_hours=route_legs[1]["duration"] / 3600.0,
    )

    start_dt = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)

    result = simulate_trip(
        start_datetime=start_dt,
        cycle_used_hours=cycle_used,
        current_label=current_location,
        pickup_label=pickup_location,
        dropoff_label=dropoff_location,
        leg_to_pickup=leg1,
        leg_to_dropoff=leg2,
    )

    daily_logs = build_daily_logs(result.events, start_dt)

    stops = [
        {
            "time": ev.start.isoformat(),
            "status": ev.status,
            "remark": ev.remark,
            "duration_hours": round(ev.hours, 2),
        }
        for ev in result.events
        if ev.remark
    ]

    response_data = {
        "route": {
            "geometry": geometry,
            "points": {
                "current": {"lat": current_pt[0], "lon": current_pt[1], "label": current_location},
                "pickup": {"lat": pickup_pt[0], "lon": pickup_pt[1], "label": pickup_location},
                "dropoff": {"lat": dropoff_pt[0], "lon": dropoff_pt[1], "label": dropoff_location},
            },
            "total_distance_miles": result.total_distance_miles,
            "total_drive_hours": result.total_drive_hours,
        },
        "stops": stops,
        "daily_logs": daily_logs,
        "summary": {
            "trip_start": start_dt.isoformat(),
            "cycle_used_before_trip": cycle_used,
            "cycle_used_after_trip": result.end_cycle_used,
            "num_days": len(daily_logs),
        },
    }

    return Response(response_data)
