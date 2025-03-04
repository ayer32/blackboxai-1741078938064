from typing import Dict, Any, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
from fastapi import HTTPException
from plugin_manager import IntegrationPlugin, PluginMetadata

class WeatherIntegrationPlugin(IntegrationPlugin):
    def __init__(self, metadata: PluginMetadata, config: Dict[str, Any]):
        super().__init__(metadata, config)
        self.api_key = config.get('api_key')
        self.units = config.get('units', 'metric')
        self.cache_duration = config.get('cache_duration', 30)
        self.cache = {}
        self.session: Optional[aiohttp.ClientSession] = None

    def setup_routes(self):
        @self.router.get("/current/{city}")
        async def get_current_weather(city: str):
            """Get current weather for a city"""
            return await self.get_weather(city)

        @self.router.get("/forecast/{city}")
        async def get_weather_forecast(city: str):
            """Get weather forecast for a city"""
            return await self.get_forecast(city)

    async def initialize(self):
        """Initialize the plugin"""
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key not configured")
        self.session = aiohttp.ClientSession()
        self.logger.info("Weather integration plugin initialized")

    async def cleanup(self):
        """Cleanup plugin resources"""
        if self.session:
            await self.session.close()
        self.logger.info("Weather integration plugin cleaned up")

    async def authenticate(self) -> bool:
        """Verify API key is valid"""
        try:
            async with self.session.get(
                "http://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": "London",
                    "appid": self.api_key,
                    "units": self.units
                }
            ) as response:
                return response.status == 200
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False

    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Any:
        """Execute weather operations"""
        operations = {
            "get_weather": self.get_weather,
            "get_forecast": self.get_forecast
        }
        
        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")
            
        return await operations[operation](**params)

    async def get_weather(self, city: str) -> Dict[str, Any]:
        """Get current weather for a city"""
        cache_key = f"weather:{city}"
        cached = self.get_from_cache(cache_key)
        if cached:
            return cached

        try:
            async with self.session.get(
                "http://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": self.units
                }
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Weather API error")
                    
                data = await response.json()
                result = {
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "timestamp": datetime.now().isoformat()
                }
                
                self.add_to_cache(cache_key, result)
                return result

        except Exception as e:
            self.logger.error(f"Error fetching weather: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch weather data")

    async def get_forecast(self, city: str) -> Dict[str, Any]:
        """Get weather forecast for a city"""
        cache_key = f"forecast:{city}"
        cached = self.get_from_cache(cache_key)
        if cached:
            return cached

        try:
            async with self.session.get(
                "http://api.openweathermap.org/data/2.5/forecast",
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": self.units
                }
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Weather API error")
                    
                data = await response.json()
                forecast = []
                
                for item in data["list"]:
                    forecast.append({
                        "timestamp": item["dt_txt"],
                        "temperature": item["main"]["temp"],
                        "description": item["weather"][0]["description"],
                        "humidity": item["main"]["humidity"],
                        "wind_speed": item["wind"]["speed"]
                    })
                
                result = {
                    "city": city,
                    "forecast": forecast,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.add_to_cache(cache_key, result)
                return result

        except Exception as e:
            self.logger.error(f"Error fetching forecast: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch forecast data")

    def get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if not expired"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(minutes=self.cache_duration):
                return data
            del self.cache[key]
        return None

    def add_to_cache(self, key: str, data: Dict[str, Any]):
        """Add data to cache"""
        self.cache[key] = (data, datetime.now())

    async def process_natural_language(self, text: str) -> Optional[Dict[str, Any]]:
        """Process natural language weather queries"""
        # Example natural language processing
        text = text.lower()
        
        if "weather" in text or "temperature" in text:
            # Extract city name (simplified example)
            words = text.split()
            if "in" in words:
                city_index = words.index("in") + 1
                if city_index < len(words):
                    city = words[city_index]
                    return await self.get_weather(city)
                    
        return None

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities for AI integration"""
        return {
            "name": "weather_integration",
            "description": "Provides weather information and forecasts",
            "commands": [
                {
                    "name": "get_weather",
                    "description": "Get current weather for a city",
                    "parameters": ["city"]
                },
                {
                    "name": "get_forecast",
                    "description": "Get weather forecast for a city",
                    "parameters": ["city"]
                }
            ],
            "natural_language": True
        }
