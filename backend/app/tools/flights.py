"""Flight search tool — uses Kiwi.com's real MCP server (free, no API key).

The server lives at https://mcp.kiwi.com/ (root path, NOT /mcp), uses the
streamable-HTTP MCP transport (responses are SSE-framed even for a single
request/response), requires `Accept: application/json, text/event-stream`,
and exposes one tool called `search-flight` — confirmed via a live
`tools/list` call. Dates must be `dd/mm/yyyy`.
"""

from __future__ import annotations

import json
from datetime import datetime

import httpx
from langchain_core.tools import tool

KIWI_MCP_URL = "https://mcp.kiwi.com/"

CABIN_CLASS_MAP = {
    "economy": "M",
    "premium_economy": "W",
    "business": "C",
    "first": "F",
}


def _to_kiwi_date(date_str: str) -> str:
    """Convert YYYY-MM-DD (our tool's input format) to Kiwi's dd/mm/yyyy."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%d/%m/%Y")


def _parse_sse_json(raw_text: str) -> dict:
    """Extract the JSON payload from an SSE-framed response body."""
    data_lines = [
        line[len("data:"):].strip()
        for line in raw_text.splitlines()
        if line.startswith("data:")
    ]
    if not data_lines:
        raise ValueError("No SSE data line in Kiwi MCP response")
    return json.loads("".join(data_lines))


def _format_duration(seconds: int | None) -> str:
    if not seconds:
        return ""
    hours, minutes = divmod(seconds // 60, 60)
    return f"{hours}h {minutes}m"


def _format_time(iso_str: str | None) -> str:
    if not iso_str:
        return ""
    try:
        return datetime.fromisoformat(iso_str).strftime("%H:%M")
    except ValueError:
        return iso_str


@tool
async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str = "",
    adults: int = 1,
    cabin_class: str = "economy",
    currency: str = "USD",
) -> str:
    """Search for real flights between two cities.

    Args:
        origin: Origin city or IATA airport code (e.g. 'Delhi' or 'DEL').
        destination: Destination city or IATA code (e.g. 'Goa' or 'GOI').
        departure_date: Departure date in YYYY-MM-DD format.
        return_date: Return date in YYYY-MM-DD format (empty for one-way).
        adults: Number of adult passengers (default 1).
        cabin_class: Cabin class — economy, premium_economy, business, first.
        currency: Currency code for prices (e.g. 'USD', 'INR', 'EUR').

    Returns:
        A formatted string of flight options with prices and details.
    """
    arguments = {
        "flyFrom": origin,
        "flyTo": destination,
        "departureDate": _to_kiwi_date(departure_date),
        "adults": adults,
        "cabinClass": CABIN_CLASS_MAP.get(cabin_class, "M"),
        "currency": currency,
        "sort": "price",
    }
    if return_date:
        arguments["returnDate"] = _to_kiwi_date(return_date)

    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "search-flight", "arguments": arguments},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                KIWI_MCP_URL,
                json=mcp_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            )
            response.raise_for_status()
            payload = _parse_sse_json(response.text)

            if "error" in payload:
                return f"Flight search error: {payload['error'].get('message', 'Unknown error')}"

            result = payload.get("result", {})
            structured = result.get("structuredContent", {})

            if structured.get("error"):
                return f"Flight search error: {structured['error']}"

            itineraries = structured.get("itineraries", [])
            if not itineraries:
                return (
                    f"No flights found from {origin} to {destination} on "
                    f"{departure_date}. Try different dates or nearby airports."
                )

            results = []
            items = []
            for it in itineraries[:5]:
                outbound = it.get("outbound") or {}
                inbound = it.get("inbound")
                segments = outbound.get("segments") or []
                airline = segments[0].get("carrierName") if segments else None

                stops = outbound.get("stops") or 0
                stops_label = "Direct" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"
                duration = _format_duration(outbound.get("durationSeconds"))
                dep_time = _format_time(outbound.get("departureTime"))
                arr_time = _format_time(outbound.get("arrivalTime"))
                price = it.get("priceFormatted") or f"{it.get('price')} {currency}"

                line = (
                    f"✈️ **Option {len(results)+1}** — {airline or 'Unknown airline'}\n"
                    f"   - Price: {price} | Duration: {duration}\n"
                    f"   - Departure: {dep_time} → Arrival: {arr_time}\n"
                    f"   - Stops: {stops_label}"
                )
                if inbound:
                    in_dep = _format_time(inbound.get("departureTime"))
                    in_arr = _format_time(inbound.get("arrivalTime"))
                    line += f"\n   - Return: {in_dep} → {in_arr}"
                if it.get("bookingUrl"):
                    line += f"\n   - [Book]({it['bookingUrl']})"

                results.append(line)
                items.append(
                    {
                        "airline": airline,
                        "price": price,
                        "duration": duration,
                        "departure": dep_time,
                        "arrival": arr_time,
                        "stops": stops_label,
                        "booking_url": it.get("bookingUrl"),
                    }
                )

            header = (
                f"✈️ **Flights: {origin} → {destination}** "
                f"({departure_date}{' - ' + return_date if return_date else ''}):\n\n"
            )
            summary = header + "\n\n".join(results)

            return json.dumps(
                {
                    "type": "flights",
                    "origin": origin,
                    "destination": destination,
                    "summary": summary,
                    "items": items,
                }
            )

    except httpx.TimeoutException:
        return "Flight search timed out. Please try again."
    except httpx.HTTPStatusError as e:
        return f"Flight search failed (HTTP {e.response.status_code}). Please try again."
    except ValueError as e:
        return f"Flight search error: could not parse response ({str(e)})."
    except Exception as e:
        return f"Flight search error: {str(e)}. Please try different search criteria."
