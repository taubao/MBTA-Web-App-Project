from flask import Flask, render_template, request
from mbta_helper import find_stop_near

app = Flask(__name__)

@app.route("/")
# Home page
def homepage():
    return render_template("index.html")


@app.get("/mbta")
# Show the input form (GET request)
def mbta_form():
    return render_template("mbta-form.html")


@app.post("/mbta")
# Handle the submitted form (POST request)
def mbta_result():

    # Read the place name from the form
    place = request.form.get("place_name")

    # If the place field is empty, show an error page
    if not place:
        return render_template("error.html", message="No place provided")

    try:
        # Find the nearest MBTA station
        station, accessible = find_stop_near(place)

        # Render the result page and pass the variables to the template
        return render_template(
            "mbta-result.html",
            place=place,
            station=station,
            accessible=accessible
        )

    except Exception:
        # If anything goes wrong, show a generic error page
        return render_template("error.html", message="Unable to find MBTA stop")


if __name__ == "__main__":
    app.run(debug=True)
