# tools/weather.py
import requests
import os
# --- THE FIX: Using standard pydantic directly ---
from pydantic import BaseModel, Field
from langchain.tools import tool
from tools.utils import get_lat_lon

OWM_KEY = os.getenv("OWM_API_KEY")

# Define inputs using standard Pydantic
class WeatherInput(BaseModel):
    location: str = Field(description="The name of the city, e.g., 'London, UK'")

@tool(args_schema=WeatherInput)
def get_current_weather(location: str) -> str:
    """Useful for getting current weather conditions for a specific city."""
    if not OWM_KEY: return "Error: OWM_API_KEY missing."

    lat, lon = get_lat_lon(location)
    if lat is None: return f"Could not find coordinates for: {location}."

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric"
        response = requests.get(url)
        if response.status_code != 200: return f"API Error: {response.status_code}"
        
        data = response.json()
        return (f"Weather in {location}: {data['weather'][0]['description'].capitalize()}. "
                f"Temp: {data['main']['temp']}°C. Humidity: {data['main']['humidity']}%.")
    except Exception as e:
        return f"Error connecting to API: {e}"