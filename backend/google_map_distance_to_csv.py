import os
import time
import urllib.parse
import requests
import csv
from dotenv import load_dotenv
from database import get_db_session
from models import Distance
from sqlmodel import select

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise RuntimeError("Please set GOOGLE_MAPS_API_KEY in your .env file")


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
    distance_text = leg["distance"]["text"]
    distance_value = leg["distance"]["value"]
    return distance_text, distance_value


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


def main():
    session = get_db_session()
    distances = session.exec(select(Distance)).fetchmany(2346)
    for dist in distances:
        origin = dist.customer_address
        destination = dist.store_address
        print(f"Processing: {origin} -> {destination}")
        try:
            distance_text, distance_value = get_distance(origin, destination)
            interactive_url = build_interactive_directions_url(
                origin, destination)
            print(f"Distance: {distance_text}, URL: {interactive_url}")
        except Exception as e:
            distance_text = str(e)
            distance_value = 0.0
            interactive_url = ""
        # Convert meters to kilometers as float
        dist.distance = float(distance_value) / 1000.0
        dist.map_url = interactive_url
    session.commit()
    session.close()
    print("Updated distance and map_url columns for first 2346 rows in distance table.")


if __name__ == "__main__":
    main()
