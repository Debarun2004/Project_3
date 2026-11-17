"""Tests for fake fleet records and dashboard endpoints."""

from fastapi.testclient import TestClient


def test_health_reports_demo_data_mode(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["dataset_status"] == "demo"


def test_driver_roster_returns_fake_records(client: TestClient) -> None:
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    drivers = response.json()
    assert len(drivers) == 7
    assert all(driver["name"] != "Demo Driver" for driver in drivers)
    assert all(len(driver["phone"]) == 10 for driver in drivers)


def test_truck_list_returns_fleet(client: TestClient) -> None:
    response = client.get("/api/v1/trucks")
    assert response.status_code == 200
    assert len(response.json()) == 8
    assert response.json()[0]["Payload"] == 2000
    assert "capacity_kg" not in response.json()[0]


def test_trip_list_labels_estimates_as_mock(client: TestClient) -> None:
    response = client.get("/api/v1/trips")
    assert response.status_code == 200
    trips = response.json()
    assert len(trips) == 7
    assert all(trip["is_mock_estimate"] for trip in trips)


def test_dashboard_summary_matches_demo_records(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    assert response.json() == {
        "drivers_total": 7,
        "drivers_on_duty": 5,
        "trucks_total": 8,
        "trucks_in_garage": 2,
        "trucks_on_road": 5,
        "trips_in_progress": 5,
        "trips_completed": 2,
    }


def test_demo_mode_rejects_writes(client: TestClient) -> None:
    response = client.post(
        "/api/v1/drivers",
        json={
            "name": "Sample Driver",
            "phone": "1234567890",
            "licence_number": "FAKE-LIC-100",
            "experience_years": 2,
        },
    )
    assert response.status_code == 503


def test_create_driver_persists_to_sql_store(mysql_client: TestClient) -> None:
    payload = {
        "name": "Sample Driver",
        "phone": "1234567890",
        "licence_number": "FAKE-LIC-100",
        "experience_years": 2,
        "rating": 4.5,
    }

    response = mysql_client.post("/api/v1/drivers", json=payload)

    assert response.status_code == 201
    created = response.json()
    assert created["id"]
    assert created["phone"] == payload["phone"]
    assert any(
        driver["id"] == created["id"]
        for driver in mysql_client.get("/api/v1/drivers").json()
    )


def test_create_truck_persists_to_sql_store(mysql_client: TestClient) -> None:
    payload = {
        "registration_number": "DEMO-NEW-001",
        "vehicle_type": "truck",
        "Payload": 5000,
    }

    response = mysql_client.post("/api/v1/trucks", json=payload)

    assert response.status_code == 201
    created = response.json()
    assert created["id"]
    assert created["Payload"] == 5000
    assert created["status"] == "garage"
    assert any(
        truck["id"] == created["id"]
        for truck in mysql_client.get("/api/v1/trucks").json()
    )


def test_create_trip_persists_to_sql_store(mysql_client: TestClient) -> None:
    payload = {
        "driver_id": "driver-demo-001",
        "truck_id": "truck-demo-001",
        "source": "Origin",
        "destination": "Destination",
        "route_name": "Sample Route",
        "parcels_total": 5,
    }

    response = mysql_client.post("/api/v1/trips", json=payload)

    assert response.status_code == 201
    created = response.json()
    assert created["id"]
    assert created["parcels_delivered"] == 0
    assert created["is_mock_estimate"] is True
    assert any(
        trip["id"] == created["id"]
        for trip in mysql_client.get("/api/v1/trips").json()
    )


def test_create_driver_validates_phone_number(mysql_client: TestClient) -> None:
    response = mysql_client.post(
        "/api/v1/drivers",
        json={
            "name": "Sample Driver",
            "phone": "12345",
            "licence_number": "FAKE-LIC-100",
            "experience_years": 2,
        },
    )

    assert response.status_code == 422


def test_create_trip_rejects_delivered_count_above_total(
    mysql_client: TestClient,
) -> None:
    response = mysql_client.post(
        "/api/v1/trips",
        json={
            "driver_id": "driver-demo-001",
            "truck_id": "truck-demo-001",
            "source": "Origin",
            "destination": "Destination",
            "route_name": "Sample Route",
            "parcels_total": 2,
            "parcels_delivered": 3,
        },
    )

    assert response.status_code == 422
