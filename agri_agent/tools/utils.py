# tools/utils.py
import requests
import os
# We use dotenv to load your OWM key specifically for this lookup function
from dotenv import load_dotenv

# Force load the .env file to get the key
load_dotenv(override=True)
OWM_KEY = os.getenv("OWM_API_KEY")

def get_lat_lon(location_name):
    """Helper function to convert a city name (e.g., "London") into Lat/Lon coordinates."""
    # If user didn't provide a name, return nothing.
    if not location_name:
        # print("Error: No location name provided for geocoding.")
        return None, None

    if not OWM_KEY:
         print("Error: OWM_API_KEY not found in .env file.")
         return None, None

    try: 
        # Use OpenWeatherMap's geocoding API endpoint
        # limit=1 means we just want the top result
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={location_name}&limit=1&appid={OWM_KEY}"
        response = requests.get(url)
        data = response.json()

        # Check if we got a valid list back and it's not empty
        if data and isinstance(data, list) and len(data) > 0:
            lat = data[0]['lat']
            lon = data[0]['lon']
            # print(f"Debug: Found coordinates for {location_name}: {lat}, {lon}")
            return lat, lon
        else:
            # print(f"Warning: Could not find coordinates for location: {location_name}")
            return None, None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None, None

# A quick test block to run if you execute this file directly: python tools/utils.py
if __name__ == "__main__":
    # This is a placeholder test. In the real app, the main agent will pass
    # whatever city the user asks for (e.g., "London") to the get_lat_lon function.
    test_city = "Mumbai"
    print(f"Testing geocoding for a sample city: {test_city}...")
    lat, lon = get_lat_lon(test_city)
    if lat:
        print(f"SUCCESS: Found at Lat: {lat}, Lon: {lon}")
        print("(Don't worry, when the main app runs, it will use whatever city the user requests!)")
    else:
        print("FAILURE: Could not geocode city.")