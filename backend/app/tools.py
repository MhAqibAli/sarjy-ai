"""External tools exposed to the LLM. Currently: Open-Meteo weather (no API key)."""
import httpx

WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "icy fog", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 71: "light snow", 73: "snow",
    75: "heavy snow", 80: "rain showers", 81: "heavy showers", 82: "violent showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm with hail",
}


async def get_weather(city: str) -> dict:
    """Geocode a city, then fetch current conditions + today's range."""
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            geo = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"},
            )
            results = geo.json().get("results") or []
            if not results:
                return {"error": f"Could not find a place called '{city}'."}
            place = results[0]

            wx = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                               "weather_code,wind_speed_10m",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "forecast_days": 1,
                    "timezone": "auto",
                },
            )
            data = wx.json()
            cur, daily = data["current"], data["daily"]
            return {
                "location": f"{place['name']}, {place.get('country', '')}".strip(", "),
                "temperature_c": cur["temperature_2m"],
                "feels_like_c": cur["apparent_temperature"],
                "humidity_pct": cur["relative_humidity_2m"],
                "wind_kmh": cur["wind_speed_10m"],
                "conditions": WEATHER_CODES.get(cur["weather_code"], "unknown"),
                "today_high_c": daily["temperature_2m_max"][0],
                "today_low_c": daily["temperature_2m_min"][0],
                "rain_chance_pct": daily["precipitation_probability_max"][0],
            }
    except Exception as exc:  # network, timeout, bad JSON
        return {"error": f"Weather service unavailable: {type(exc).__name__}"}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather and today's forecast for a city. "
                           "Use the user's remembered home_city if they don't name one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. 'Karachi'"}
                },
                "required": ["city"],
            },
        },
    }
]

TOOL_HANDLERS = {"get_weather": get_weather}
