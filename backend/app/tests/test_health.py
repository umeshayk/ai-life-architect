from __future__ import annotations

from fastapi.testclient import TestClient


def test_live_health_returns_success(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "healthy"
    assert response.headers["x-request-id"]


def test_ready_health_returns_dependency_details(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready", headers={"x-request-id": "test-request"})

    assert response.status_code in {200, 503}
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["request_id"] == "test-request"
    dependency_names = {dependency["name"] for dependency in payload["data"]["dependencies"]}
    assert {"database", "worker", "ai_provider"}.issubset(dependency_names)


def test_health_details_returns_structured_response(client: TestClient) -> None:
    response = client.get("/api/v1/health/details")

    assert response.status_code in {200, 503}
    payload = response.json()
    assert set(payload.keys()) == {"success", "data", "error", "meta"}
