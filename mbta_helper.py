import os
import json
import urllib.request
import urllib.parse

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment variables
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
MBTA_API_KEY = os.getenv("MBTA_API_KEY")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")  # NEW

# Optional: helpful error messages if keys are missing
if MAPBOX_TOKEN is None:
    raise RuntimeError("MAPBOX_TOKEN is not set. Check your .env file.")
if MBTA_API_KEY is None:
    raise RuntimeError("MBTA_API_KEY is not set. Check your .env file.")
if TICKETMASTER_API_KEY is None:  # NEW
    raise RuntimeError("TICKETMASTER_API_KEY is not set. Check your .env file.")

# Useful base URLs (you need to add the appropriate parameters for each API request)
MAPBOX_BASE_URL = "https://api.mapbox.com/search/searchbox/v1/forward"
MBTA_BASE_URL = "https://api-v3.mbta.com/"
TICKETMASTER_BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"  # NEW


# A little bit of scaffolding if you want to use it
def get_json(url: str) -> dict:
    """
    Given a properly formatted URL for a JSON web API request, return a Python JSON object containing the response to that request.

    Both get_lat_lng() and get_nearest_station() might need to use this function.
    """
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())


def get_lat_lng(place_name: str) -> tuple[str, str]:
    """
    Given a place name or address, return a (latitude, longitude) tuple with the coordinates of the given place.

    See https://docs.mapbox.com/api/search/search-box/#search-request for Mapbox Search API URL formatting requirements.
    """
    # Format the location name so it can go into a URL
    query = urllib.parse.quote(place_name)
    url = f"{MAPBOX_BASE_URL}?q={query}&access_token={MAPBOX_TOKEN}"

    data = get_json(url)

    # # If Mapbox can't find any information, display an error message
    if "features" not in data or len(data["features"]) == 0:
        raise RuntimeError("No results found for that location.")

    # Set the coordinates to [longitude, latitude]
    coords = data["features"][0]["geometry"]["coordinates"]
    lng, lat = coords[0], coords[1]

    return str(lat), str(lng)


def get_nearest_station(latitude: str, longitude: str) -> tuple[str, bool]:
    """
    Given latitude and longitude strings, return a (station_name, wheelchair_accessible) tuple for the nearest MBTA station to the given coordinates. wheelchair_accessible is True if the stop is marked as accessible, False otherwise.

    See https://api-v3.mbta.com/docs/swagger/index.html#/Stop/ApiWeb_StopController_index for URL formatting requirements for the 'GET /stops' API.
    """
    url = (
        f"{MBTA_BASE_URL}stops?"
        f"filter[latitude]={latitude}&filter[longitude]={longitude}"
        f"&api_key={MBTA_API_KEY}&sort=distance"
    )

    data = get_json(url)

    # If the API did not return any stops, return an error message
    if "data" not in data or len(data["data"]) == 0:
        raise RuntimeError("No nearby MBTA stops found.")

    # The first stop in the list is the closest one because we sorted by distance
    nearest = data["data"][0]

    # Extract the stop's name from the JSON structure
    name = nearest["attributes"]["name"]

    # For the MBTA API, 1 = wheelchair accessible
    wheelchair = nearest["attributes"]["wheelchair_boarding"] == 1

    return name, wheelchair


def find_stop_near(place_name: str) -> tuple[str, bool]:
    """
    Given a place name or address, return the nearest MBTA stop and whether it is wheelchair accessible.

    This function might use all the functions above.
    """
    # Get the location's coordinates using the Mapbox geocoding function.
    lat, lng = get_lat_lng(place_name)

    # Find the nearest station
    return get_nearest_station(lat, lng)


# --------------------------------------------------------------
# WOW FEATURE: Ticketmaster Nearby Events
# --------------------------------------------------------------
def get_nearby_events(latitude: str, longitude: str, radius: int = 5):
    """
    Given latitude and longitude strings, return a list of nearby Ticketmaster events.
    Each event contains the event name, date, venue, and a link to the event page.
    """

    # Build the Ticketmaster API request URL
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "latlong": f"{latitude},{longitude}",
        "radius": radius,
        "size": 5
    }

    url = TICKETMASTER_BASE_URL + "?" + urllib.parse.urlencode(params)

    try:
        data = get_json(url)

        # If Ticketmaster has no events nearby, return an empty list
        if "_embedded" not in data:
            return []

        events_raw = data["_embedded"]["events"]
        events_clean = []

        # Extract only the information we care about from each event
        for e in events_raw:
            name = e.get("name", "Unknown event")
            date = e["dates"]["start"].get("localDate", "Unknown date")
            venue = e["_embedded"]["venues"][0].get("name", "Unknown venue")
            link = e.get("url", "")

            events_clean.append({
                "name": name,
                "date": date,
                "venue": venue,
                "url": link
            })

        return events_clean

    except Exception:
        return []


def main():
    """
    You should test all the above functions here
    """
    test_place = "Wellesley"
    station, accessible = find_stop_near(test_place)

    print("Nearest MBTA Station:", station)
    print("Wheelchair Accessible:", accessible)

    lat, lng = get_lat_lng(test_place)
    events = get_nearby_events(lat, lng)

    print("\nNearby Events:")
    for e in events:
        print(f"- {e['name']} on {e['date']} at {e['venue']}")


if __name__ == "__main__":
    main()
