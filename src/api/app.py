from flask import Flask, jsonify
import sqlite3
from src.consumer.ride_consumer import DATABASE_FILE, get_analytics

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
