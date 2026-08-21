import os
import sys
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app
from backend.app.database.connection import get_db_session

client = TestClient(app)


def mock_get_db_session():
    """Mock database session dependency generator for isolated offline unit tests."""
    db_session = MagicMock()

    # Mock air quality daily summary response
    mock_aq_row = MagicMock()
    mock_aq_row.mappings.return_value.all.return_value = [
        {"reading_date": "2026-08-20", "avg_concentration": 22.4, "max_aqi": 72}
    ]

    # Mock earthquake events response
    mock_eq_row = MagicMock()
    mock_eq_row.mappings.return_value.all.return_value = [
        {
            "event_id": "us7000m123",
            "event_time": "2026-08-20T08:14:22Z",
            "magnitude": 5.4,
            "magnitude_category": "Moderate",
            "place": "14 km E of Hiroo, Japan",
            "region": "Japan",
            "latitude": 42.28,
            "longitude": 143.42,
            "depth_km": 35.2,
            "tsunami": 0,
        }
    ]

    # Mock regional summary response
    mock_regional_row = MagicMock()
    mock_regional_row.mappings.return_value.all.return_value = [
        {
            "region": "Japan",
            "total_events": 10,
            "max_magnitude": 5.4,
            "avg_depth_km": 35.2,
            "tsunami_alerts": 0,
        }
    ]

    # Mock monthly category response
    mock_monthly_row = MagicMock()
    mock_monthly_row.mappings.return_value.all.return_value = [
        {
            "month": "2026-08",
            "magnitude_category": "Moderate",
            "event_count": 10,
        }
    ]

    # Mock trends response
    mock_trends_row = MagicMock()
    mock_trends_row.mappings.return_value.all.return_value = [
        {
            "date": "2026-08-20",
            "pm25_avg": 22.4,
            "earthquake_count": 5,
        }
    ]

    # Configure session execute return value behavior
    def execute_side_effect(sql, *args, **kwargs):
        sql_str = str(sql)
        if "WITH dates AS" in sql_str or "generate_series" in sql_str:
            return mock_trends_row
        elif "GROUP BY region" in sql_str:
            return mock_regional_row
        elif "GROUP BY month" in sql_str:
            return mock_monthly_row
        elif "earthquake_events" in sql_str:
            return mock_eq_row
        elif "air_quality_readings" in sql_str:
            return mock_aq_row
        return mock_aq_row

    db_session.execute.side_effect = execute_side_effect
    yield db_session


app.dependency_overrides[get_db_session] = mock_get_db_session


def test_get_air_quality_visualization():
    response = client.get("/api/visualization/air-quality?city=Coimbatore&parameter=pm25")
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Coimbatore"
    assert data["parameter"] == "pm25"
    assert data["total_records"] == 1
    assert data["data"][0]["avg_concentration"] == 22.4
    assert data["data"][0]["max_aqi"] == 72


def test_get_earthquake_visualization():
    response = client.get("/api/visualization/earthquakes?min_magnitude=2.5")
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] == 1
    assert data["events"][0]["event_id"] == "us7000m123"
    assert data["events"][0]["magnitude"] == 5.4
    assert data["events"][0]["magnitude_category"] == "Moderate"


def test_get_analytics_trends():
    response = client.get("/api/analytics/trends")
    assert response.status_code == 200
    data = response.json()
    assert data["total_days"] == 1
    assert data["trends"][0]["date"] == "2026-08-20"
    assert data["trends"][0]["pm25_avg"] == 22.4
    assert data["trends"][0]["earthquake_count"] == 5
