import os
import time
import urllib.parse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise RuntimeError("Please set GOOGLE_MAPS_API_KEY in your .env file")

# -----------------------------------
# Input Data
# -----------------------------------
origin = "Howrah Station, West Bengal"
destination = "Netaji Subhash Chandra Bose International Airport, Kolkata"
waypoints = []  # e.g. ["Shyambazar, Kolkata", "Lake Town, Kolkata"]
mode = "driving"
departure_time = int(time.time())

# -----------------------------------
# 1) Fetch distance from Google Directions API
# -----------------------------------


def get_distance(origin, destination, waypoints=None, mode="driving", departure_time=None):
    url = "https://maps.googleapis.com/maps/api/directions/json"

    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "key": API_KEY
    }

    if waypoints:
        params["waypoints"] = "|".join(waypoints)

    if departure_time and mode == "driving":
        params["departure_time"] = departure_time

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    if data.get("status") != "OK":
        raise RuntimeError(
            f"Directions API error: {data.get('status')} - {data.get('error_message')}"
        )

    leg = data["routes"][0]["legs"][0]
    distance_text = leg["distance"]["text"]     # e.g. "12.4 km"
    distance_value = leg["distance"]["value"]   # meters

    return distance_text, distance_value


# -----------------------------------
# 2) Build Interactive Google Maps URL
# -----------------------------------
def build_interactive_directions_url(origin, destination, waypoints=None, mode="driving"):
    base = "https://www.google.com/maps/dir/?api=1"

    params = {
        "origin": origin,
        "destination": destination,
        "travelmode": mode
    }

    if waypoints:
        params["waypoints"] = "|".join(waypoints)

    qs = urllib.parse.urlencode(params, safe="|")
    return f"{base}&{qs}"


# -----------------------------------
# Main Execution
# -----------------------------------
distance_text, distance_value = get_distance(
    origin,
    destination,
    waypoints,
    mode,
    departure_time
)

interactive_url = build_interactive_directions_url(
    origin,
    destination,
    waypoints,
    mode
)

print("\nINTERACTIVE GOOGLE MAPS URL:")
print(interactive_url)

print("\nDISTANCE:")
print(distance_text)
# print(distance_value)  # meters if needed
