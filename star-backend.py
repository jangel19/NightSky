from flask import Flask, request, jsonify, render_template
import requests
from dotenv import load_dotenv
import os
import base64

# load .env credentials
load_dotenv()

API_ID = os.getenv("API_ID")
API_SECRET = os.getenv("API_SECRET")
print(" API_ID:", repr(API_ID))
print(" API_SECRET:", repr(API_SECRET))

app = Flask(__name__)

from requests.exceptions import ReadTimeout

#test to see if the api is responding
@app.route("/test_connection", methods=["GET"])
def test_connection():
    credentials = f"{API_ID}:{API_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }

    res = requests.get("https://api.astronomyapi.com/api/v2/bodies", headers=headers)
    return jsonify({
        "status": res.status_code,
        "response": res.json()
    })

@app.route("/get_coordinates", methods=["POST"])
def get_coordinates():
    location = request.json.get("location")
    print("requested location:", location)

    GEO_API_KEY = os.getenv("GEO_API_KEY")
    print(" GEO_API_KEY loaded:", GEO_API_KEY is not None)

    res = requests.get(f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={GEO_API_KEY}")
    print(" OpenCage URL:", res.url)

    data = res.json()
    if not data["results"]:
        print(" OpenCage response:", data)
        return jsonify({"error": "Location not found"}), 400

    coords = data["results"][0]["geometry"]
    print(" Found coordinates:", coords)
    return jsonify(coords)

@app.route("/get_chart", methods=["POST"])
def get_chart():
    try:
        data = request.json
        observer = data["observer"]
        view = data["view"]

        credentials = f"{API_ID}:{API_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.astronomyapi.com/api/v2/studio/star-chart",
            headers=headers,
            json={
                "observer": observer,
                "view": view
            },
            timeout=60
        )

        print(" Chart API response status:", response.status_code)
        print(" Chart API response JSON:", response.text)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch chart", "details": response.text}), response.status_code

        return jsonify(response.json())

    except ReadTimeout:
        return jsonify({"error": "AstronomyAPI timed out. Please try again later."}), 504
    
    from flask import render_template

@app.route("/")
def home():
    return render_template("main.html")
    
if __name__ == "__main__":
    app.run(debug=True)