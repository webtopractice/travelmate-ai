"""Shared geocoding + Overpass POI search helpers.

POI search uses the Overpass API (OpenStreetMap data) — free, no API key.

Geocoding does NOT use Nominatim/Photon: both returned 403s in testing (their
abuse-detection blocks many shared/cloud egress IPs) and Nominatim also
prohibits this kind of automated per-request use without heavier rate
limiting. Instead we reuse OpenWeather's classic `/weather` endpoint (same
key already required for get_weather) purely to resolve a place name to
lat/lon — it turns out to disambiguate regional/state names (e.g. "Goa",
"Kerala") noticeably better than the dedicated geocoders we tried anyway, and
keeps location resolution consistent with the weather tool.
"""

from __future__ import annotations

import httpx

from app.config import get_settings

# Public Overpass mirrors, tried in order — the main instance occasionally
# rate-limits or is briefly overloaded, so a couple of free fallbacks avoid a
# single point of failure without needing any keys.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

USER_AGENT = "TravelMateAI-Hackathon/1.0 (contact: travelmate-ai@example.com)"


async def geocode_city(city: str) -> tuple[float, float] | None:
    """Get (lat, lon) for a city/region name via OpenWeather's geocoding."""
    api_key = get_settings().OPENWEATHER_API_KEY
    if not api_key or api_key == "your_openweather_api_key_here":
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            coord = data.get("coord")
            if coord and "lat" in coord and "lon" in coord:
                return coord["lat"], coord["lon"]
    except Exception:
        pass
    return None


async def query_overpass(query: str) -> list[dict]:
    """Run an Overpass QL query, trying each mirror in turn. Returns the 'elements' list.

    Uses GET with the query in the URL (not POST) — some Overpass front-ends
    reject POST bodies from httpx clients with a 406 even though the same
    query works fine as a GET query string.
    """
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=25.0, headers={"User-Agent": USER_AGENT}) as client:
        for url in OVERPASS_URLS:
            try:
                resp = await client.get(url, params={"data": query})
                resp.raise_for_status()
                return resp.json().get("elements", [])
            except Exception as e:
                last_error = e
                continue
    if last_error:
        raise last_error
    return []


def infer_category(tags: dict) -> str:
    """Best-effort human-readable category from whichever OSM tag is present."""
    for key in ("tourism", "historic", "natural", "amenity", "leisure", "shop"):
        val = tags.get(key)
        if val and val != "yes":
            return val.replace("_", " ").title()
        if val == "yes" and key == "historic":
            return "Historic Site"
    return ""


def element_coords(element: dict) -> tuple[float, float] | None:
    """Nodes have lat/lon directly; ways/relations need 'out center' for a center point."""
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    center = element.get("center")
    if center:
        return center.get("lat"), center.get("lon")
    return None
