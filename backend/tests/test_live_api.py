"""
Unit tests for FastAPI Real-Time API endpoints (/api/live/*) and WebSocket connection.
"""

import os
import sys
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app

client = TestClient(app)


def test_get_live_air_quality_endpoint():
    mock_data = [
        {
            "measurement_id": 101,
            "location_id": 8914,
            "parameter": "pm25",
            "value": 14.5,
            "latitude": 11.0168,
            "longitude": 76.9558,
            "reading_timestamp": "2026-08-24T12:00:00Z",
        }
    ]
    with patch("backend.app.routers.live.store.get_recent_air_quality", return_value=mock_data):
        response = client.get("/api/live/air-quality")
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "kafka"
        assert data["count"] == 1
        assert data["records"][0]["measurement_id"] == 101


def test_get_live_earthquakes_endpoint():
    mock_events = [
        {
            "event_id": "us7000live",
            "event_time": "2026-08-24T12:00:00Z",
            "magnitude": 4.8,
            "latitude": 35.0,
            "longitude": 140.0,
            "depth_km": 20.0,
        }
    ]
    with patch("backend.app.routers.live.store.get_recent_earthquakes", return_value=mock_events):
        response = client.get("/api/live/earthquakes")
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "kafka"
        assert data["count"] == 1
        assert data["events"][0]["event_id"] == "us7000live"


def test_get_live_health_endpoint():
    with patch("backend.app.routers.live.store.is_healthy", return_value=True), patch(
        "backend.app.routers.live.check_kafka_health", return_value=False
    ):
        response = client.get("/api/live/health")
        assert response.status_code == 200
        data = response.json()
        assert data["redis"] == "healthy"
        assert data["kafka"] == "unhealthy"


def test_websocket_live_endpoint_snapshot():
    mock_aq = [{"measurement_id": 55, "value": 12.0}]
    mock_eq = [{"event_id": "eq99", "magnitude": 3.5}]

    with patch("backend.app.routers.live.store.get_recent_air_quality", return_value=mock_aq), patch(
        "backend.app.routers.live.store.get_recent_earthquakes", return_value=mock_eq
    ):
        with client.websocket_connect("/api/live/ws") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "SNAPSHOT"
            assert len(data["air_quality"]) == 1
            assert len(data["earthquakes"]) == 1
            assert data["air_quality"][0]["measurement_id"] == 55
            assert data["earthquakes"][0]["event_id"] == "eq99"
