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


def test_get_analytics_trends_no_dates():
    """Verify analytics trends endpoint functions with default date parameters (no dates specified)."""
    response = client.get("/api/analytics/trends")
    assert response.status_code == 200
    data = response.json()
    assert data["total_days"] == 1
    assert data["trends"][0]["date"] == "2026-08-20"
    assert data["trends"][0]["pm25_avg"] == 22.4
    assert data["trends"][0]["earthquake_count"] == 5


def test_get_analytics_trends_with_explicit_dates():
    """Verify analytics trends endpoint functions with explicit start_date and end_date query parameters."""
    response = client.get("/api/analytics/trends?start_date=2026-08-01&end_date=2026-08-25")
    assert response.status_code == 200
    data = response.json()
    assert data["total_days"] == 1
    assert data["trends"][0]["date"] == "2026-08-20"
    assert data["trends"][0]["pm25_avg"] == 22.4
    assert data["trends"][0]["earthquake_count"] == 5


def test_analytics_repository_query_parameters():
    """Directly test AnalyticsRepository.get_independent_trends passes correct parameters and syntax."""
    from backend.app.database.repository import AnalyticsRepository

    mock_session = MagicMock()
    mock_row = MagicMock()
    mock_row.mappings.return_value.all.return_value = [
        {"date": "2026-08-20", "pm25_avg": 18.5, "earthquake_count": 2}
    ]
    mock_session.execute.return_value = mock_row

    # Test 1: with no dates
    results_no_dates = AnalyticsRepository.get_independent_trends(mock_session, start_date=None, end_date=None)
    assert len(results_no_dates) == 1
    assert results_no_dates[0]["date"] == "2026-08-20"
    assert results_no_dates[0]["pm25_avg"] == 18.5
    assert results_no_dates[0]["earthquake_count"] == 2

    call_args_no_dates = mock_session.execute.call_args
    sql_text_no_dates = str(call_args_no_dates[0][0])
    params_no_dates = call_args_no_dates[0][1]
    assert "CAST(:start_date AS DATE)" in sql_text_no_dates
    assert "CAST(:end_date AS DATE)" in sql_text_no_dates
    assert params_no_dates == {"start_date": None, "end_date": None}

    # Test 2: with explicit dates
    results_with_dates = AnalyticsRepository.get_independent_trends(
        mock_session, start_date="2026-08-01", end_date="2026-08-25"
    )
    assert len(results_with_dates) == 1
    assert results_with_dates[0]["date"] == "2026-08-20"

    call_args_with_dates = mock_session.execute.call_args
    params_with_dates = call_args_with_dates[0][1]
    assert params_with_dates == {"start_date": "2026-08-01", "end_date": "2026-08-25"}

