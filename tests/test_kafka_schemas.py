"""
Unit tests for Kafka Air Quality and Earthquake message schema validation and serialization.
"""

from kafka.schemas.air_quality import AirQualityMessage, validate_air_quality_message
from kafka.schemas.earthquake import EarthquakeMessage, validate_earthquake_message


def test_air_quality_message_valid():
    msg = AirQualityMessage(
        measurement_id=12345,
        location_id=8914,
        parameter="pm25",
        value=22.4,
        latitude=11.0168,
        longitude=76.9558,
        reading_timestamp="2026-08-24T12:00:00Z",
        city="Coimbatore",
        country="IN",
    )
    d = msg.to_dict()
    assert d["measurement_id"] == 12345
    assert d["value"] == 22.4
    assert d["source"] == "openaq"

    is_valid, reason = validate_air_quality_message(d)
    assert is_valid is True
    assert reason == ""


def test_air_quality_message_invalid_missing_field():
    d = {
        "location_id": 8914,
        "parameter": "pm25",
        "value": 22.4,
    }
    is_valid, reason = validate_air_quality_message(d)
    assert is_valid is False
    assert "Missing required field" in reason


def test_air_quality_message_invalid_coordinates():
    d = {
        "measurement_id": 123,
        "location_id": 8914,
        "parameter": "pm25",
        "value": 22.4,
        "latitude": 195.0,  # Invalid lat > 90
        "longitude": 76.9558,
        "reading_timestamp": "2026-08-24T12:00:00Z",
    }
    is_valid, reason = validate_air_quality_message(d)
    assert is_valid is False
    assert "out of range" in reason


def test_earthquake_message_valid():
    msg = EarthquakeMessage(
        event_id="us7000xyz",
        event_time="2026-08-24T12:00:00Z",
        magnitude=5.4,
        latitude=42.28,
        longitude=143.42,
        depth_km=35.2,
        place="42 km E of Hokkaido, Japan",
    )
    d = msg.to_dict()
    assert d["event_id"] == "us7000xyz"
    assert d["magnitude"] == 5.4
    assert d["source"] == "usgs"

    is_valid, reason = validate_earthquake_message(d)
    assert is_valid is True
    assert reason == ""


def test_earthquake_message_invalid_type():
    d = {
        "event_id": "us7000xyz",
        "event_time": "2026-08-24T12:00:00Z",
        "magnitude": "NOT_A_NUMBER",
        "latitude": 42.28,
        "longitude": 143.42,
        "depth_km": 35.2,
    }
    is_valid, reason = validate_earthquake_message(d)
    assert is_valid is False
    assert "must be numeric" in reason
