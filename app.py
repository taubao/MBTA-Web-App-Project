from flask import Flask, render_template, request
from mbta_helper import (
    find_stop_near,
    get_lat_lng,
    get_nearby_events,
    get_current_weather,
)

app = Flask(__name__)


@app.route("/")
def homepage():
    # Home page
    return render_template("index.html")


@app.get("/mbta")
def mbta_form():
    # Show the input form (GET request)
    return render_template("mbta-form.html")


@app.post("/mbta")
def mbta_result():
    # Handle the submitted form (POST request)
    place = request.form.get("place_name")

    # If the place field is empty, show an error page
    if not place:
        return render_template("error.html", message="No place provided")

    try:
        # Get latitude & longitude
        lat, lng = get_lat_lng(place)

        # Find nearest MBTA station
        station, accessible = find_stop_near(place)

        # Fetch nearby Ticketmaster events
        events = get_nearby_events(lat, lng)

        # NEW — Fetch weather data
        weather = get_current_weather(lat, lng)

        # Render results page
        return render_template(
            "mbta-result.html",
            place=place,
            station=station,
            accessible=accessible,
            events=events,
            weather=weather,  # NEW
        )

    except Exception:
        return render_template("error.html", message="Unable to find MBTA stop")


if __name__ == "__main__":
    app.run(debug=True)
