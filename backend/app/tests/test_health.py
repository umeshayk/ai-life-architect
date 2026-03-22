from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check_uses_standard_contract():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["error"] is None
    assert payload["data"]["status"] == "OK"
    assert payload["data"]["ports"]["backend"] == 8004
    assert payload["meta"] == {}


def test_readiness_check_includes_foundation_dependencies():
    response = client.get("/api/v1/health/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["dependencies"]["database"]["status"] == "CONFIGURED"
    assert payload["data"]["dependencies"]["ollama"]["model"] == "phi3:mini"
