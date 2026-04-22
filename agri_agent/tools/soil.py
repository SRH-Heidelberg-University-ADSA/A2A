# tools/soil.py
import requests
import os
import time
# --- THE FIX: Using standard pydantic directly ---
from pydantic import BaseModel, Field
from langchain.tools import tool
from tools.utils import get_lat_lon

AGRO_KEY = os.getenv("AGRO_API_KEY")

class SoilInput(BaseModel):
    location: str = Field(description="The name of the city or region.")

@tool(args_schema=SoilInput)
def get_soil_data(location: str) -> str:
    """Useful for getting current soil temperature and moisture for a location."""
    if not AGRO_KEY: return "Error: AGRO_API_KEY missing."

    lat, lon = get_lat_lon(location)
    if lat is None: return f"Could not find coordinates for: {location}."

    try:
        current_time = int(time.time())
        url = f"http://api.agromonitoring.com/agro/1.0/soil?lat={lat}&lon={lon}&t={current_time}&appid={AGRO_KEY}"
        response = requests.get(url)
        
        if response.status_code == 200 and 't0' in response.json():
            data = response.json()
            temp_c = round(data['t0'] - 273.15, 1)
            moisture = data.get('moisture', 'N/A')
            return (f"Soil data for {location} (10cm depth): Temp: {temp_c}°C. "
                    f"Moisture: {moisture} (0=dry, 1=wet).")
        else:
            return f"No current satellite soil data available for {location}."
    except Exception as e:
        return f"Error connecting to API: {e}"