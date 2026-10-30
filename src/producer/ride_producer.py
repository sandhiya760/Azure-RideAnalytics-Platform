
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from azure.eventhub import EventHubProducerClient, EventData


# -------------------------------
# Project Configuration
# -------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")


# -------------------------------
# Ride Event Configuration
# -------------------------------

CITIES = [
    "Chennai",
    "Bengaluru",
    "Hyderabad",
    "Mumbai",
    "Delhi"
]

RIDE_STATUSES = [
    "booked",
    "completed",
    "cancelled"
]

STATUS_WEIGHTS = [50, 40, 10]

EVENT_INTERVAL = 2  # Seconds between events


# -------------------------------
# File Configuration
# -------------------------------

DATA_DIR = PROJECT_ROOT / "data"
EVENT_FILE = DATA_DIR / "rides.jsonl"


# -------------------------------
# Azure Event Hubs Configuration
# -------------------------------

EVENT_HUB_CONNECTION_STRING = os.getenv(
    "EVENT_HUB_PRODUCER_CONNECTION_STRING"
)

EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")


# -------------------------------
# Ride Event Generator
# -------------------------------

def generate_ride_event():
    """Generate a simulated ride event."""

    status = random.choices(
        RIDE_STATUSES,
        weights=STATUS_WEIGHTS,
        k=1
    )[0]

    event = {
        "event_id": str(uuid4()),
        "ride_id": f"RIDE-{uuid4().hex[:8].upper()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "city": random.choice(CITIES),
        "distance_km": round(random.uniform(2, 25), 2),
        "fare": (
            0.0 if status == "cancelled"
            else round(random.uniform(80, 600), 2)
        ),
        "status": status
    }

    return event


# -------------------------------
# Save Event Locally
# -------------------------------

def save_event(event):
    """Append one ride event to the local JSONL file."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with EVENT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")
        file.flush()


# -------------------------------
# Publish Event to Azure Event Hubs
# -------------------------------

def publish_event(event, producer):
    """Publish one ride event to Azure Event Hubs."""

    event_data = EventData(json.dumps(event))

    batch = producer.create_batch()
    batch.add(event_data)

    producer.send_batch(batch)


# -------------------------------
# Producer Execution
# -------------------------------

def run_producer():

    if not EVENT_HUB_CONNECTION_STRING:
        raise ValueError(
            "EVENT_HUB_PRODUCER_CONNECTION_STRING is missing from .env"
        )

    if not EVENT_HUB_NAME:
        raise ValueError(
            "EVENT_HUB_NAME is missing from .env"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 55)
    print("       RIDE EVENT PRODUCER STARTED")
    print("=" * 55)

    print(f"Local event file: {EVENT_FILE}")
    print(f"Azure Event Hub: {EVENT_HUB_NAME}")
    print(f"Event interval: {EVENT_INTERVAL} seconds")
    print("Publishing events to Azure Event Hubs...")
    print("Press Ctrl+C to stop.\n")

    producer = None

    try:
        producer = EventHubProducerClient.from_connection_string(
            conn_str=EVENT_HUB_CONNECTION_STRING,
            eventhub_name=EVENT_HUB_NAME
        )

        print("Connected to Azure Event Hubs successfully!\n")

        while True:

            event = generate_ride_event()

            # Save event to local JSONL file
            save_event(event)

            # Publish event to Azure Event Hubs
            publish_event(event, producer)

            print("Event saved locally and published to Azure:")
            print(json.dumps(event, indent=4))
            print("-" * 55, flush=True)

            time.sleep(EVENT_INTERVAL)

    except KeyboardInterrupt:
        print("\nRide Event Producer stopped.")

    finally:
        if producer is not None:
            producer.close()
            print("Azure Event Hubs connection closed.")


# -------------------------------
# Main Entry Point
# -------------------------------

if __name__ == "__main__":
    run_producer()
