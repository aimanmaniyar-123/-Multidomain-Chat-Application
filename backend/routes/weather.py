import httpx
import os

async def get_weather(city: str):
    url = f"http://api.weatherapi.com/v1/current.json"
    params = {"key": os.getenv("WEATHER_API_KEY"), "q": city}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()
