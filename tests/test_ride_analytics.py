
import pytest

import src.consumer.ride_consumer as consumer


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    """Use an isolated temporary SQLite database for each test."""

    test_data_dir = tmp_path / "data"
    test_data_dir.mkdir()

    test_db = test_data_dir / "test_rides.db"

    monkeypatch.setattr(consumer, "DATA_DIR", test_data_dir)
    monkeypatch.setattr(consumer, "DATABASE_FILE", test_db)

    consumer.initialize_database()

    return test_db


@pytest.fixture
def valid_event():
    """Return a sample valid ride event."""

    return {
        "event_id": "event-001",
        "ride_id": "RIDE-001",
        "timestamp": "2026-10-31T10:00:00Z",
        "city": "Chennai",
        "distance_km": 10.5,
        "fare": 150.0,
        "status": "completed"
    }


# 1. EVENT VALIDATION TESTS

def test_valid_event(valid_event):
    is_valid, message = consumer.validate_event(valid_event)

    assert is_valid is True
    assert message == "Event is valid"


def test_missing_required_field(valid_event):
    valid_event.pop("city")

    is_valid, message = consumer.validate_event(valid_event)

    assert is_valid is False
    assert message == "Missing field: city"


def test_invalid_ride_status(valid_event):
    valid_event["status"] = "unknown"

    is_valid, message = consumer.validate_event(valid_event)

    assert is_valid is False
    assert message == "Invalid ride status"


def test_negative_distance(valid_event):
    valid_event["distance_km"] = -5

    is_valid, message = consumer.validate_event(valid_event)

    assert is_valid is False
    assert message == "Distance and fare cannot be negative"


def test_cancelled_ride_must_have_zero_fare(valid_event):
    valid_event["status"] = "cancelled"
    valid_event["fare"] = 100

    is_valid, message = consumer.validate_event(valid_event)

    assert is_valid is False
    assert message == "Cancelled rides must have zero fare"


# 2. EVENT PROCESSING TESTS

def test_process_valid_event(test_database, valid_event):
    result = consumer.process_event(valid_event)

    assert result == "processed"


def test_duplicate_event_is_ignored(
    test_database, valid_event
):
    first_result = consumer.process_event(valid_event)
    second_result = consumer.process_event(valid_event)

    assert first_result == "processed"
    assert second_result == "duplicate"


def test_invalid_event_is_rejected(
    test_database, valid_event
):
    valid_event["fare"] = -100

    result = consumer.process_event(valid_event)

    assert result == "invalid"


# 3. ANALYTICS TESTS

def test_empty_database_analytics(test_database):
    analytics = consumer.get_analytics()

    assert analytics["total_rides"] == 0
    assert analytics["completed_rides"] == 0
    assert analytics["booked_rides"] == 0
    assert analytics["cancelled_rides"] == 0
    assert analytics["total_revenue"] == 0
    assert analytics["cancellation_rate"] == 0
    assert analytics["city_wise"] == []


def test_ride_analytics_calculation(
    test_database, valid_event
):
    consumer.process_event(valid_event)

    booked_event = {
        **valid_event,
        "event_id": "event-002",
        "ride_id": "RIDE-002",
        "city": "Bengaluru",
        "status": "booked",
        "fare": 200
    }

    cancelled_event = {
        **valid_event,
        "event_id": "event-003",
        "ride_id": "RIDE-003",
        "city": "Chennai",
        "status": "cancelled",
        "fare": 0
    }

    consumer.process_event(booked_event)
    consumer.process_event(cancelled_event)

    analytics = consumer.get_analytics()

    assert analytics["total_rides"] == 3
    assert analytics["completed_rides"] == 1
    assert analytics["booked_rides"] == 1
    assert analytics["cancelled_rides"] == 1
    assert analytics["total_revenue"] == 150.0
    assert analytics["cancellation_rate"] == 33.33
    assert len(analytics["city_wise"]) == 2
