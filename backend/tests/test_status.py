import os
import sys
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app

client = TestClient(app)


@patch("backend.app.services.prefect_service.PrefectService.get_flow_run_status", new_callable=AsyncMock)
def test_get_status_completed(mock_status):
    mock_status.return_value = {
        "flow_run_id": "00000000-0000-0000-0000-000000000001",
        "status": "COMPLETED",
        "state_type": "COMPLETED",
        "message": "Flow run completed successfully",
    }

    response = client.get("/api/status/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 200
    data = response.json()
    assert data["flow_run_id"] == "00000000-0000-0000-0000-000000000001"
    assert data["status"] == "COMPLETED"
    assert data["state_type"] == "COMPLETED"


@patch("backend.app.services.prefect_service.PrefectService.get_flow_run_status", new_callable=AsyncMock)
def test_get_status_not_found(mock_status):
    mock_status.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Prefect flow run not found",
    )

    response = client.get("/api/status/00000000-0000-0000-0000-000000000999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Prefect flow run not found"


@patch("backend.app.services.prefect_service.PrefectService.get_flow_run_status", new_callable=AsyncMock)
def test_get_status_prefect_unavailable(mock_status):
    mock_status.side_effect = HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Prefect server unavailable",
    )

    response = client.get("/api/status/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 503
    assert response.json()["detail"] == "Prefect server unavailable"
