
"""Hotel search tool — POI data from OpenStreetMap's Overpass API (free, no key)."""

from __future__ import annotations

import json

import httpx
from langchain_core.tools import tool

from app.config import get_settings
from app.tools.osm import geocode_city, query_overpass

# OSM tags covering accommodation types
HOTEL_TAGS = "hotel|hostel|guest_house|motel|apartment|chalet"


@tool
async def search_hotels(
    destination: str,
    budget_level: str = "medium",
) -> str:
    """Search for hotels and accommodations at a destination.

    Args:
        destination: City name (e.g. 'Goa', 'Paris', 'Tokyo').
        budget_level: Budget level — 'budget', 'medium', or 'luxury'.

    Returns:
        A formatted string of hotel/accommodation options.
    """
    api_key = get_settings().OPENWEATHER_API_KEY
    if not api_key or api_key == "your_openweather_api_key_here":
        return (
            f"🏨 Hotel search for {destination} needs location lookup, which uses "
            f"OPENWEATHER_API_KEY. Set that in your .env file to enable it."
        )

    coords = await geocode_city(destination)
    if not coords:
        return f"Could not find location '{destination}'. Please check the city name."

    lat, lon = coords

    query = f"""
    [out:json][timeout:20];
    nwr["tourism"~"^({HOTEL_TAGS})$"](around:10000,{lat},{lon});
    out center 20;
    """

    try:
        elements = await query_overpass(query)

        if not elements:
            return f"No hotels found in {destination}. Try a nearby larger city."

        price_map = {
            "budget": "₹1,500-3,000/night",
            "medium": "₹3,000-7,000/night",
            "luxury": "₹7,000-15,000+/night",
        }
        est_price = price_map.get(budget_level, "₹3,000-7,000/night")

        results = []
        items = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name or not name.strip():
                continue

            addr_parts = [
                tags.get("addr:street"),
                tags.get("addr:suburb") or tags.get("addr:city"),
            ]
            location = ", ".join(p for p in addr_parts if p)
            hotel_type = tags.get("tourism", "").replace("_", " ").title()
            stars = tags.get("stars")

            detail_text = ""
            if location:
                detail_text += f" | Location: {location}"
            if hotel_type:
                detail_text += f" | Type: {hotel_type}"

            star_display = f"{'⭐' * int(float(stars))}" if stars and stars.replace(".", "").isdigit() else "⭐⭐⭐"

            results.append(
                f"🏨 **Option {len(results)+1}** — {name} {star_display}\n"
                f"   - Estimated Price: ~{est_price}{detail_text}\n"
            )

            items.append(
                {
                    "name": name,
                    "rating": float(stars) if stars and stars.replace(".", "").isdigit() else None,
                    "price_estimate": est_price,
                    "location": location or None,
                    "type": hotel_type or None,
                }
            )

            if len(results) >= 5:
                break

        if not results:
            return (
                f"Found accommodation locations in {destination} but couldn't "
                f"get usable details. Try searching for '{destination} hotels' or "
                f"a specific area within the city."
            )

        header = f"🏨 **Hotels in {destination}** ({budget_level.title()} range):\n\n"
        summary = header + "\n".join(results)

        return json.dumps(
            {
                "type": "hotels",
                "destination": destination,
                "summary": summary,
                "items": items,
            }
        )

    except httpx.TimeoutException:
        return "Hotel search timed out. Please try again."
    except Exception as e:
        return f"Hotel search error: {str(e)}"
