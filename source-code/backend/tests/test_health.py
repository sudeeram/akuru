from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_does_not_require_database() -> None:
    response = TestClient(app, base_url="http://localhost").get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "akuru-api"}
