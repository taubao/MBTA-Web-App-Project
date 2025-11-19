from flask import Flask, render_template, request
from mbta_helper import find_stop_near

app = Flask(__name__)

@app.route("/")
# This is the home page.
# It shows a simple welcome message and a link to the MBTA search page.
def homepage():
    return render_template("index.html")

@app.get("/mbta")
# This route shows the input form。 
# The user types a place name here
def mbta_form():
    return render_template("mbta-form.html")

@app.post("/mbta")
# Read the place name from the form, call our helper function, and then show the result page.
def mbta_result():
    place = request.form.get("place_name")

    if not place:
        return render_template("error.html", message="No place provided")

    try:
        station, accessible = find_stop_near(place)
        return render_template(
            "mbta-result.html",
            place=place,
            station=station,
            accessible=accessible
        )
    except Exception:
        return render_template("error.html", message="Unable to find MBTA stop")

if __name__ == "__main__":
    app.run(debug=True)
