"""Connectivity and validation tests for the FastAPI endpoints."""

from fastapi.testclient import TestClient

from app.schemas import RouteComparisonResponse, RouteOptimizationResponse

VALID_INPUT = {
    "source": "Kolkata",
    "destination": "Howrah",
    "vehicle_type": "truck",
    "payload_kg": 500,
    "dispatch_time": "2026-11-06T10:00:00+05:30",
    "optimization_preference": "balanced",
}


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["server_status"] == "ok"


def test_compare_accepts_valid_input(client: TestClient) -> None:
    response = client.post("/routes/compare", json=VALID_INPUT)
    assert response.status_code == 200
    assert response.json()["is_mock"] is True


def test_optimize_accepts_valid_input(client: TestClient) -> None:
    response = client.post("/routes/optimize", json=VALID_INPUT)
    assert response.status_code == 200
    assert response.json()["selected_preference"] == "balanced"


def test_missing_source_returns_validation_error(client: TestClient) -> None:
    request = VALID_INPUT.copy()
    request.pop("source")
    assert client.post("/routes/compare", json=request).status_code == 422


def test_negative_payload_returns_validation_error(client: TestClient) -> None:
    request = VALID_INPUT | {"payload_kg": -1}
    assert client.post("/routes/compare", json=request).status_code == 422


def test_invalid_vehicle_type_returns_validation_error(client: TestClient) -> None:
    request = VALID_INPUT | {"vehicle_type": "bus"}
    assert client.post("/routes/compare", json=request).status_code == 422


def test_invalid_optimization_preference_returns_validation_error(
    client: TestClient,
) -> None:
    request = VALID_INPUT | {"optimization_preference": "cheapest"}
    assert client.post("/routes/optimize", json=request).status_code == 422


def test_invalid_dispatch_time_returns_validation_error(client: TestClient) -> None:
    request = VALID_INPUT | {"dispatch_time": "tomorrow morning"}
    assert client.post("/routes/compare", json=request).status_code == 422


def test_identical_source_and_destination_are_rejected(client: TestClient) -> None:
    request = VALID_INPUT | {"destination": "kolkata"}
    assert client.post("/routes/compare", json=request).status_code == 422


def test_response_matches_defined_schemas(client: TestClient) -> None:
    compare_response = client.post("/routes/compare", json=VALID_INPUT)
    optimize_response = client.post("/routes/optimize", json=VALID_INPUT)

    assert RouteComparisonResponse.model_validate(compare_response.json())
    assert RouteOptimizationResponse.model_validate(optimize_response.json())
