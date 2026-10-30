
from flask import Flask, jsonify
from pathlib import Path
import sqlite3

# Import analytics logic from consumer
from src.consumer.ride_consumer import DATABASE_FILE, get_analytics

# Initialize Flask application
app = Flask(__name__)


# -----------------------------------
# 1. Health Check Endpoint
# -----------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Ride Analytics API"
    }), 200


# -----------------------------------
# 2. Overall Ride Analytics
# -----------------------------------

@app.route("/analytics", methods=["GET"])
def analytics():
    try:
        data = get_analytics()
        return jsonify(data), 200

    except sqlite3.Error as error:
        return jsonify({
            "error": "Unable to retrieve analytics",
            "details": str(error)
        }), 500


# -----------------------------------
# 3. City-wise Analytics
# -----------------------------------

@app.route("/analytics/cities", methods=["GET"])
def city_analytics():
    try:
        data = get_analytics()

        return jsonify({
            "city_wise": data["city_wise"]
        }), 200

    except sqlite3.Error as error:
        return jsonify({
            "error": "Unable to retrieve city analytics",
            "details": str(error)
        }), 500


# -----------------------------------
# 4. Run Flask Application
# -----------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
