"""Activity & attraction search tool — POI data from OpenStreetMap's Overpass API (free, no key)."""

from __future__ import annotations

import json

import httpx
from langchain_core.tools import tool

from app.config import get_settings
from app.tools.osm import geocode_city, infer_category, query_overpass

# Map user-friendly interest categories to a single Overpass tag filter.
# Kept to ONE filter per interest (no unions of multiple clauses) so each
# search is one small, fast Overpass query instead of a heavier combined one.
INTEREST_FILTERS = {
    "culture": '["tourism"~"museum|gallery"]',
    "nature": '["natural"~"beach|wood|water"]',
    "adventure": '["leisure"~"sports_centre|water_park"]',
    "food": '["amenity"~"restaurant|cafe|fast_food"]',
    "history": '["historic"]',
    "shopping": '["shop"~"mall|department_store"]',
    "nightlife": '["amenity"~"nightclub|bar|pub"]',
    "religious": '["amenity"="place_of_worship"]',
    "beaches": '["natural"="beach"]',
    "family": '["tourism"~"zoo|theme_park"]',
    "sightseeing": '["tourism"~"attraction|viewpoint"]',
}


@tool
async def search_activities(
    destination: str,
    interests: str = "sightseeing",
) -> str:
    """Search for activities, attractions, and things to do at a destination.

    Args:
        destination: City name (e.g. 'Goa', 'Paris', 'Tokyo').
        interests: A single interest, e.g. 'culture', 'food', 'nature'.
                   Options: culture, nature, adventure, food, history,
                   shopping, nightlife, religious, beaches, family, sightseeing.
                   Only the first interest is used (kept simple/fast).

    Returns:
        A formatted string of activity and attraction suggestions.
    """
    api_key = get_settings().OPENWEATHER_API_KEY
    if not api_key or api_key == "your_openweather_api_key_here":
        return (
            f"🎯 Activity search for {destination} needs location lookup, which uses "
            f"OPENWEATHER_API_KEY. Set that in your .env file to enable it."
        )

    coords = await geocode_city(destination)
    if not coords:
        return f"Could not find location '{destination}'. Please check the city name."

    lat, lon = coords

    primary_interest = interests.split(",")[0].strip().lower()
    tag_filter = INTEREST_FILTERS.get(primary_interest, INTEREST_FILTERS["sightseeing"])

    # One simple, fast query: a single tag filter, small radius, small limit.
    query = f"""
    [out:json][timeout:15];
    nwr{tag_filter}(around:8000,{lat},{lon});
    out center 15;
    """

    try:
        elements = await query_overpass(query)

        if not elements:
            return (
                f"No activities found in {destination} matching '{interests}'. "
                f"Try broader interests like 'sightseeing' or 'culture'."
            )

        results = []
        items = []
        seen_names = set()
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name or not name.strip() or name in seen_names:
                continue
            seen_names.add(name)

            category = infer_category(tags)
            description = tags.get("description") or tags.get("cuisine")

            entry = f"🎯 **{name}**\n"
            if category:
                entry += f"   - Type: {category}\n"
            if description:
                entry += f"   - {description}\n"

            results.append(entry)
            items.append(
                {
                    "name": name,
                    "rating": None,
                    "category": category or None,
                    "description": description or None,
                }
            )

            if len(results) >= 6:
                break

        if not results:
            return (
                f"Found locations in {destination} but couldn't get usable details. "
                f"The destination has attractions matching your interests!"
            )

        header = (
            f"🎯 **Things to do in {destination}** "
            f"(interests: {interests}):\n\n"
        )
        summary = header + "\n".join(results)

        return json.dumps(
            {
                "type": "activities",
                "destination": destination,
                "summary": summary,
                "items": items,
            }
        )

    except httpx.TimeoutException:
        return "Activity search timed out. Please try again."
    except Exception as e:
        return f"Activity search error: {str(e)}"
