import os
import sys
from unittest.mock import patch
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app

client = TestClient(app)


@patch("backend.app.services.prefect_service.PrefectService.trigger_pipeline")
def test_trigger_openaq_valid(mock_trigger):
    mock_trigger.return_value = "mock_openaq_flow_run_123"

    payload = {
        "pipeline": "openaq",
        "city": "Coimbatore",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "radius": 25000,
        "measurement_limit": 2000,
    }

    response = client.post("/api/trigger", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "triggered"
    assert data["pipeline"] == "openaq"
    assert data["flow_run_id"] == "mock_openaq_flow_run_123"


@patch("backend.app.services.prefect_service.PrefectService.trigger_pipeline")
def test_trigger_usgs_valid(mock_trigger):
    mock_trigger.return_value = "mock_usgs_flow_run_456"

    payload = {
        "pipeline": "usgs",
        "start_date": "2026-01-01",
        "end_date": "2026-08-20",
        "min_magnitude": 2.5,
        "limit": 1000,
    }

    response = client.post("/api/trigger", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "triggered"
    assert data["pipeline"] == "usgs"
    assert data["flow_run_id"] == "mock_usgs_flow_run_456"


def test_trigger_invalid_pipeline():
    payload = {
        "pipeline": "invalid_pipeline",
        "city": "Coimbatore",
    }
    response = client.post("/api/trigger", json=payload)
    assert response.status_code == 422


def test_trigger_invalid_latitude():
    payload = {
        "pipeline": "openaq",
        "city": "Coimbatore",
        "latitude": 120.0,  # Invalid: > 90
        "longitude": 76.9558,
        "radius": 25000,
        "measurement_limit": 2000,
    }
    response = client.post("/api/trigger", json=payload)
    assert response.status_code == 422


def test_trigger_invalid_usgs_dates():
    payload = {
        "pipeline": "usgs",
        "start_date": "2026-08-20",
        "end_date": "2026-01-01",  # Invalid: start > end
        "min_magnitude": 2.5,
        "limit": 1000,
    }
    response = client.post("/api/trigger", json=payload)
    assert response.status_code == 422
