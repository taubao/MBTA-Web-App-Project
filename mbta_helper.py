import os
import json
import urllib.request
import urllib.parse

from dotenv import load_dotenv

load_dotenv()

# Get API keys from environment variables
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
MBTA_API_KEY = os.getenv("MBTA_API_KEY")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Error check: helpful error messages if keys are missing
if MAPBOX_TOKEN is None:
    raise RuntimeError("MAPBOX_TOKEN is not set. Check your .env file.")
if MBTA_API_KEY is None:
    raise RuntimeError("MBTA_API_KEY is not set. Check your .env file.")
if TICKETMASTER_API_KEY is None:
    raise RuntimeError("TICKETMASTER_API_KEY is not set. Check your .env file.")
if OPENWEATHER_API_KEY is None:
    raise RuntimeError("OPENWEATHER_API_KEY is not set. Check your .env file.")

# Useful base URLs
MAPBOX_BASE_URL = "https://api.mapbox.com/search/searchbox/v1/forward"
MBTA_BASE_URL = "https://api-v3.mbta.com/"
TICKETMASTER_BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_json(url: str) -> dict:
    """
    Open a URL and return the JSON response as a Python dictionary.
    Used by other functions when calling web APIs.
    """
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())


def get_lat_lng(place_name: str) -> tuple[str, str]:
    """
    Take a place name (like 'Boston Common') and return its latitude and longitude.
    This uses the Mapbox API to look up the location.
    """
    query = urllib.parse.quote(place_name)
    url = f"{MAPBOX_BASE_URL}?q={query}&access_token={MAPBOX_TOKEN}"

    data = get_json(url)

    # If the API could not find the place, stop the program
    if "features" not in data or len(data["features"]) == 0:
        raise RuntimeError("No results found for that location.")

    # Get the coordinates of the location
    coords = data["features"][0]["geometry"]["coordinates"]
    lng, lat = coords[0], coords[1]

    # Return the coordinates as strings
    return str(lat), str(lng)


def get_nearest_station(latitude: str, longitude: str) -> tuple[str, bool]:
    """
    Use MBTA's API to find the closest station to the given latitude and longitude.
    Returns the station name and whether it is wheelchair accessible.
    """
    url = (
        f"{MBTA_BASE_URL}stops?"
        f"filter[latitude]={latitude}&filter[longitude]={longitude}"
        f"&api_key={MBTA_API_KEY}&sort=distance"
    )

    data = get_json(url)

    # If MBTA does not return any stops, print a unique message
    if "data" not in data or len(data["data"]) == 0:
        raise RuntimeError("No nearby MBTA stops found.")

    nearest = data["data"][0]
    name = nearest["attributes"]["name"]

    # 1 = wheelchair accessible
    wheelchair = nearest["attributes"]["wheelchair_boarding"] == 1

    return name, wheelchair


def find_stop_near(place_name: str) -> tuple[str, bool]:
    """
    Given a place name, find its coordinates and then return the nearest MBTA stop.
    Returns both the station name and whether it is accessible.
    """
    lat, lng = get_lat_lng(place_name)
    return get_nearest_station(lat, lng)


# ----------------------------------------------------
# Wow! OpenWeather
def get_current_weather(latitude: str, longitude: str, units: str = "imperial"):
    """
    Return the current weather near this location.
    The function returns a dictionary with temperature and a short text description.
    """
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": OPENWEATHER_API_KEY,
        "units": units,
    }

    url = OPENWEATHER_BASE_URL + "?" + urllib.parse.urlencode(params)

    try:
        data = get_json(url)

        main = data.get("main", {})
        weather_list = data.get("weather", [])

        temp = main.get("temp")
        feels_like = main.get("feels_like")
        description = weather_list[0].get("description", "") if weather_list else ""

        # Return a dictionary with weather info
        return {
            "temp": temp,
            "feels_like": feels_like,
            "description": description,
        }

    except Exception:
        return {}


# ----------------------------------------------------
# Wow! Ticketmaster Nearby Events
def get_nearby_events(latitude: str, longitude: str, radius: int = 5):
    """
    Given latitude and longitude strings, return a list of nearby Ticketmaster events.
    Each event contains the event name, date, venue, and a link to the event page.
    """
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "latlong": f"{latitude},{longitude}",
        "radius": radius,
        "size": 5,
    }

    url = TICKETMASTER_BASE_URL + "?" + urllib.parse.urlencode(params)

    try:
        data = get_json(url)

        # If Ticketmaster has no events, return an empty list
        if "_embedded" not in data:
            return []

        events_raw = data["_embedded"]["events"]
        events_clean = []

        for e in events_raw:
            name = e.get("name", "Unknown event")
            date = e["dates"]["start"].get("localDate", "Unknown date")
            venue = e["_embedded"]["venues"][0].get("name", "Unknown venue")
            link = e.get("url", "")

            events_clean.append({
                "name": name,
                "date": date,
                "venue": venue,
                "url": link,
            })

        return events_clean
    
    # If anything goes wrong, return an empty list
    except Exception:
        return []

# ----------------------------------------------------
# Main
def main():
    """
    Test the functions above.
    """
    test_place = "Wellesley"

    station, accessible = find_stop_near(test_place)
    print("Nearest MBTA Station:", station)
    print("Wheelchair Accessible:", accessible)

    lat, lng = get_lat_lng(test_place)

    # Test Ticketmaster events
    events = get_nearby_events(lat, lng)
    print("\nNearby Events:")
    for e in events:
        print(f"- {e['name']} on {e['date']} at {e['venue']}")

    # Test OpenWeather
    weather = get_current_weather(lat, lng)
    print("\nCurrent Weather:")
    if weather:
        print(f"Temperature: {weather['temp']}°F (feels like {weather['feels_like']}°F)")
        print(f"Condition: {weather['description']}")
    else:
        print("Weather data not available.")


if __name__ == "__main__":
    main()
