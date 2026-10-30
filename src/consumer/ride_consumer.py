
import json
import os
import sqlite3
import math
from pathlib import Path

from dotenv import load_dotenv
from azure.eventhub import EventHubConsumerClient


# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
DATABASE_FILE = DATA_DIR / "ride_analytics.db"

VALID_STATUSES = {"booked", "completed", "cancelled"}

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")


# ==================================================
# 2. AZURE EVENT HUB CONFIGURATION
# ==================================================

EVENT_HUB_CONNECTION_STRING = os.getenv(
    "EVENT_HUB_CONSUMER_CONNECTION_STRING"
)

EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")

EVENT_HUB_CONSUMER_GROUP = os.getenv(
    "EVENT_HUB_CONSUMER_GROUP",
    "$Default"
)


# ==================================================
# 3. DATABASE INITIALIZATION
# ==================================================

def initialize_database():
    """Create SQLite database and ride_events table."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ride_events (
                event_id TEXT PRIMARY KEY,
                ride_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                city TEXT NOT NULL,
                distance_km REAL NOT NULL,
                fare REAL NOT NULL,
                status TEXT NOT NULL
            )
        """)

    print("SQLite database initialized successfully!")


# ==================================================
# 4. EVENT VALIDATION
# ==================================================

def validate_event(event):
    """Validate an incoming ride event."""

    required_fields = [
        "event_id",
        "ride_id",
        "timestamp",
        "city",
        "distance_km",
        "fare",
        "status"
    ]

    if not isinstance(event, dict):
        return False, "Event must be a JSON object"

    for field in required_fields:
        if field not in event or event[field] is None:
            return False, f"Missing field: {field}"

    # Validate text fields
    for field in ["event_id", "ride_id", "timestamp", "city"]:
        if not isinstance(event[field], str) or not event[field].strip():
            return False, f"Invalid field: {field}"

    # Validate ride status
    if event["status"] not in VALID_STATUSES:
        return False, "Invalid ride status"

    # Validate numeric fields
    try:
        distance = float(event["distance_km"])
        fare = float(event["fare"])
    except (ValueError, TypeError):
        return False, "Distance and fare must be numeric"

    if not math.isfinite(distance) or not math.isfinite(fare):
        return False, "Distance and fare must be finite numbers"

    if distance < 0 or fare < 0:
        return False, "Distance and fare cannot be negative"

    if event["status"] == "cancelled" and fare != 0:
        return False, "Cancelled rides must have zero fare"

    return True, "Event is valid"


# ==================================================
# 5. PROCESS AND STORE EVENTS
# ==================================================

def process_event(event):
    """Validate and insert an event into SQLite."""

    is_valid, message = validate_event(event)

    if not is_valid:
        print(f"Rejected event: {message}")
        return "invalid"

    with sqlite3.connect(DATABASE_FILE) as connection:
        cursor = connection.execute("""
            INSERT OR IGNORE INTO ride_events (
                event_id,
                ride_id,
                timestamp,
                city,
                distance_km,
                fare,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event["event_id"],
            event["ride_id"],
            event["timestamp"],
            event["city"],
            float(event["distance_km"]),
            float(event["fare"]),
            event["status"]
        ))

        if cursor.rowcount == 0:
            print(f"Duplicate event ignored: {event['event_id']}")
            return "duplicate"

    print(
        f"Processed: {event['ride_id']} | "
        f"{event['city']} | {event['status']}"
    )

    return "processed"


# ==================================================
# 6. ANALYTICS AGGREGATION
# ==================================================

def get_analytics():
    """Calculate ride analytics from stored events."""

    with sqlite3.connect(DATABASE_FILE) as connection:

        connection.row_factory = sqlite3.Row

        summary = connection.execute("""
            SELECT
                COUNT(*) AS total_rides,

                SUM(CASE
                    WHEN status = 'completed' THEN 1
                    ELSE 0
                END) AS completed_rides,

                SUM(CASE
                    WHEN status = 'booked' THEN 1
                    ELSE 0
                END) AS booked_rides,

                SUM(CASE
                    WHEN status = 'cancelled' THEN 1
                    ELSE 0
                END) AS cancelled_rides,

                SUM(CASE
                    WHEN status = 'completed' THEN fare
                    ELSE 0
                END) AS total_revenue

            FROM ride_events
        """).fetchone()

        city_data = connection.execute("""
            SELECT
                city,
                COUNT(*) AS total_rides,
                SUM(CASE
                    WHEN status = 'completed' THEN fare
                    ELSE 0
                END) AS revenue

            FROM ride_events
            GROUP BY city
            ORDER BY total_rides DESC
        """).fetchall()

    total = summary["total_rides"] or 0
    cancelled = summary["cancelled_rides"] or 0

    return {
        "total_rides": total,
        "completed_rides": summary["completed_rides"] or 0,
        "booked_rides": summary["booked_rides"] or 0,
        "cancelled_rides": cancelled,
        "total_revenue": round(summary["total_revenue"] or 0, 2),
        "cancellation_rate": round(
            (cancelled / total * 100) if total else 0, 2
        ),
        "city_wise": [
            dict(row) for row in city_data
        ]
    }


# ==================================================
# 7. AZURE EVENT HUB CONSUMER
# ==================================================

def on_event(partition_context, event):
    """Receive an event from Azure Event Hubs."""

    if event is None:
        return

    try:
        event_body = event.body_as_str(encoding="UTF-8")
        ride_event = json.loads(event_body)

        result = process_event(ride_event)

        if result == "processed":
            print(
                f"Received from Azure Event Hubs | "
                f"Partition: {partition_context.partition_id}"
            )

    except json.JSONDecodeError:
        print("Rejected malformed JSON event from Azure Event Hubs.")

    except Exception as error:
        print(f"Error processing incoming event: {error}")


def on_error(partition_context, error):
    """Handle Event Hubs partition errors."""

    partition_id = (
        partition_context.partition_id
        if partition_context else "Unknown"
    )

    print(
        f"Event Hubs error | "
        f"Partition: {partition_id} | {error}"
    )


# ==================================================
# 8. CONTINUOUS EVENT CONSUMER
# ==================================================

def run_consumer():
    """Continuously receive events from Azure Event Hubs."""

    if not EVENT_HUB_CONNECTION_STRING:
        raise ValueError(
            "EVENT_HUB_CONSUMER_CONNECTION_STRING is missing from .env"
        )

    if not EVENT_HUB_NAME:
        raise ValueError(
            "EVENT_HUB_NAME is missing from .env"
        )

    initialize_database()

    print("\n" + "=" * 55)
    print("       AZURE RIDE ANALYTICS CONSUMER STARTED")
    print("=" * 55)

    print(f"Event Hub: {EVENT_HUB_NAME}")
    print(f"Consumer group: {EVENT_HUB_CONSUMER_GROUP}")
    print(f"Database: {DATABASE_FILE}")
    print("Waiting for Azure events...\n")

    client = EventHubConsumerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STRING,
        consumer_group=EVENT_HUB_CONSUMER_GROUP,
        eventhub_name=EVENT_HUB_NAME
    )

    try:
        with client:
            client.receive(
                on_event=on_event,
                on_error=on_error,
                starting_position="-1"
            )

    except KeyboardInterrupt:
        print("\nAzure Event Hubs Consumer stopped.")

    finally:
        analytics = get_analytics()

        print("\n========== RIDE ANALYTICS ==========")
        print(json.dumps(analytics, indent=4))
        print("====================================")


# ==================================================
# 9. MAIN ENTRY POINT
# ==================================================

if __name__ == "__main__":
    run_consumer()
