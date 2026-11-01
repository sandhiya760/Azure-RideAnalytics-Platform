from flask import Flask, jsonify, Response, request, g
import sqlite3
import time

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from src.consumer.ride_consumer import DATABASE_FILE, get_analytics

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "rideanalytics_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "rideanalytics_api_request_duration_seconds",
    "API request processing time",
    ["method", "endpoint"]
)


@app.before_request
def start_timer():
    g.start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    if request.path != "/metrics":
        duration = time.perf_counter() - g.start_time
        endpoint = request.endpoint or "unmatched"

        REQUEST_COUNT.labels(
            request.method, endpoint, str(response.status_code)
        ).inc()

        REQUEST_LATENCY.labels(
            request.method, endpoint
        ).observe(duration)

    return response


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Ride Analytics API'
    }), 200


@app.route('/analytics', methods=['GET'])
def analytics():
    try:
        data = get_analytics()
        return jsonify(data), 200
    except sqlite3.Error as error:
        return jsonify({
            'error': 'Unable to retrieve analytics',
            'details': str(error)
        }), 500


@app.route('/analytics/cities', methods=['GET'])
def city_analytics():
    try:
        data = get_analytics()
        return jsonify({'city_wise': data['city_wise']}), 200
    except sqlite3.Error as error:
        return jsonify({
            'error': 'Unable to retrieve city analytics',
            'details': str(error)
        }), 500


@app.route('/metrics', methods=['GET'])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
