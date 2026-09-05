"""Weather forecast tool — uses OpenWeather API (free tier, 60 calls/min)."""

from __future__ import annotations

import json

import httpx
from langchain_core.tools import tool

from app.config import get_settings


@tool
async def get_weather(
    city: str,
    date: str = "",
) -> str:
    """Get current weather and forecast for a city.

    Args:
        city: City name (e.g. 'Goa', 'Paris', 'Tokyo').
        date: Optional target date in YYYY-MM-DD format for forecast context.

    Returns:
        A formatted string with weather information.
    """
    settings = get_settings()
    api_key = settings.OPENWEATHER_API_KEY

    if not api_key or api_key == "your_openweather_api_key_here":
        return (
            f"🌤️ **Weather info for {city}**\n"
            f"Weather API key not configured. Based on general knowledge, "
            f"please check weather websites for accurate forecasts.\n"
            f"Tip: Set OPENWEATHER_API_KEY in your .env file "
            f"(free at openweathermap.org)."
        )

    base_url = "https://api.openweathermap.org/data/2.5"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get current weather
            resp = await client.get(
                f"{base_url}/weather",
                params={
                    "q": city,
                    "appid": api_key,
                    "units": "metric",
                },
            )
            resp.raise_for_status()
            current = resp.json()

            temp = current["main"]["temp"]
            feels_like = current["main"]["feels_like"]
            humidity = current["main"]["humidity"]
            description = current["weather"][0]["description"].title()
            wind = current["wind"]["speed"]

            # Also get 5-day forecast
            forecast_text = ""
            forecast_items = []
            try:
                forecast_resp = await client.get(
                    f"{base_url}/forecast",
                    params={
                        "q": city,
                        "appid": api_key,
                        "units": "metric",
                        "cnt": 16,  # ~2 days of 3-hour intervals
                    },
                )
                if forecast_resp.status_code == 200:
                    forecast_data = forecast_resp.json()
                    forecasts = forecast_data.get("list", [])

                    # Summarize daily highs/lows
                    daily = {}
                    for item in forecasts:
                        day = item["dt_txt"].split(" ")[0]
                        t = item["main"]["temp"]
                        if day not in daily:
                            daily[day] = {"high": t, "low": t, "desc": ""}
                        daily[day]["high"] = max(daily[day]["high"], t)
                        daily[day]["low"] = min(daily[day]["low"], t)
                        daily[day]["desc"] = item["weather"][0]["description"]

                    forecast_lines = []
                    for day, info in list(daily.items())[:3]:
                        forecast_lines.append(
                            f"   - {day}: {info['low']:.0f}°C – "
                            f"{info['high']:.0f}°C, {info['desc'].title()}"
                        )
                        forecast_items.append(
                            {
                                "day": day,
                                "low": round(info["low"], 1),
                                "high": round(info["high"], 1),
                                "description": info["desc"].title(),
                            }
                        )
                    if forecast_lines:
                        forecast_text = (
                            "\n📅 **Upcoming Forecast:**\n"
                            + "\n".join(forecast_lines)
                        )
            except Exception:
                pass

            date_note = f" (for your trip around {date})" if date else ""

            summary = (
                f"🌤️ **Weather in {city}**{date_note}:\n\n"
                f"   - 🌡️ Temperature: {temp:.1f}°C (feels like {feels_like:.1f}°C)\n"
                f"   - ☁️ Conditions: {description}\n"
                f"   - 💧 Humidity: {humidity}%\n"
                f"   - 💨 Wind: {wind} m/s\n"
                f"{forecast_text}\n"
            )

            return json.dumps(
                {
                    "type": "weather",
                    "city": city,
                    "summary": summary,
                    "current": {
                        "temp": round(temp, 1),
                        "feels_like": round(feels_like, 1),
                        "humidity": humidity,
                        "description": description,
                        "wind": wind,
                    },
                    "forecast": forecast_items,
                }
            )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"City '{city}' not found. Please check the city name."
        elif e.response.status_code == 401:
            return "Weather API key is invalid. Please check OPENWEATHER_API_KEY."
        return f"Weather API error (HTTP {e.response.status_code})."
    except httpx.TimeoutException:
        return "Weather request timed out. Please try again."
    except Exception as e:
        return f"Weather error: {str(e)}"
