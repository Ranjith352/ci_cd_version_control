from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_get_health_endpoint():
    """Verify GET /health returns HTTP 200 OK and expected healthy response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "environmental-intelligence-api",
    }
