"""Weather tool using Open-Meteo API."""

import httpx

from bot.tools.base import BaseTool, ToolResult


class WeatherTool(BaseTool):
    """Get weather information using Open-Meteo (free, no API key)."""
    
    name = "weather"
    description = "Get current weather and forecast for a location. Provides temperature, conditions, humidity, and wind."
    parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name or location (e.g., 'Kyiv', 'London, UK')",
            },
        },
        "required": ["location"],
    }
    
    GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    
    async def execute(self, location: str) -> ToolResult:
        """Get weather for location."""
        try:
            # 1. Geocode location
            coords = await self._geocode(location)
            if coords is None:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Location not found: {location}",
                )
            
            lat, lon, name = coords
            
            # 2. Get weather
            weather = await self._get_weather(lat, lon)
            
            output = f"""🌤️ Погода в {name}:
• Температура: {weather['temp']}°C (відчувається як {weather['feels_like']}°C)
• Умови: {weather['conditions']}
• Вологість: {weather['humidity']}%
• Вітер: {weather['wind_speed']} км/год
• Опади: {weather['precipitation']} мм"""
            
            return ToolResult(
                success=True,
                output=output,
                data=weather,
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Weather fetch failed: {e}",
            )
    
    async def _geocode(self, location: str) -> tuple[float, float, str] | None:
        """Get coordinates for location."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.GEOCODE_URL,
                params={"name": location, "count": 1, "language": "uk"},
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                return None
            
            result = data["results"][0]
            return (
                result["latitude"],
                result["longitude"],
                result.get("name", location),
            )
    
    async def _get_weather(self, lat: float, lon: float) -> dict:
        """Get current weather for coordinates."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.WEATHER_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                    "timezone": "auto",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            current = data["current"]
            
            return {
                "temp": current["temperature_2m"],
                "feels_like": current["apparent_temperature"],
                "humidity": current["relative_humidity_2m"],
                "precipitation": current["precipitation"],
                "wind_speed": current["wind_speed_10m"],
                "conditions": self._weather_code_to_text(current["weather_code"]),
            }
    
    def _weather_code_to_text(self, code: int) -> str:
        """Convert WMO weather code to text."""
        codes = {
            0: "Ясно ☀️",
            1: "Переважно ясно 🌤️",
            2: "Частково хмарно ⛅",
            3: "Хмарно ☁️",
            45: "Туман 🌫️",
            48: "Туман з інеєм 🌫️",
            51: "Легка мряка 🌧️",
            53: "Помірна мряка 🌧️",
            55: "Сильна мряка 🌧️",
            61: "Легкий дощ 🌧️",
            63: "Помірний дощ 🌧️",
            65: "Сильний дощ 🌧️",
            71: "Легкий сніг 🌨️",
            73: "Помірний сніг 🌨️",
            75: "Сильний сніг 🌨️",
            80: "Легкі зливи 🌦️",
            81: "Помірні зливи 🌦️",
            82: "Сильні зливи 🌦️",
            95: "Гроза ⛈️",
            96: "Гроза з градом ⛈️",
            99: "Сильна гроза з градом ⛈️",
        }
        return codes.get(code, f"Код: {code}")
