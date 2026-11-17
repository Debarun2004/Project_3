"""Control-room messages and route plans."""

from fastapi.testclient import TestClient


def test_message_reaches_only_its_driver_and_can_be_marked_read(client: TestClient) -> None:
    sent = client.post("/api/v1/messages", json={"driver_id": "DRV-001", "text": "  Avoid the market road  "})
    assert sent.status_code == 201
    assert sent.json()["text"] == "Avoid the market road"
    client.post("/api/v1/messages", json={"driver_id": "DRV-002", "text": "Hello"})

    mine = client.get("/api/v1/dispatch", params={"driver_id": "DRV-001"}).json()["messages"]
    assert [m["text"] for m in mine] == ["Avoid the market road"]
    assert mine[0]["read"] is False

    assert client.post("/api/v1/messages/read", json={"driver_id": "DRV-001"}).status_code == 204
    assert client.get("/api/v1/dispatch", params={"driver_id": "DRV-001"}).json()["messages"][0]["read"] is True
    assert len(client.get("/api/v1/dispatch").json()["messages"]) == 2


def test_plan_is_stored_and_announced(client: TestClient) -> None:
    assert client.post("/api/v1/plans", json={"driver_id": "DRV-003", "pref": "greenest"}).status_code == 201
    client.post("/api/v1/plans", json={"driver_id": "DRV-003", "pref": "balanced"})
    state = client.get("/api/v1/dispatch").json()
    assert state["plans"] == {"DRV-003": "balanced"}
    assert [m["pref"] for m in state["messages"]] == ["balanced", "greenest"]


def test_unknown_driver_and_bad_option_are_rejected(client: TestClient) -> None:
    assert client.post("/api/v1/messages", json={"driver_id": "DRV-999", "text": "hi"}).status_code == 404
    assert client.post("/api/v1/plans", json={"driver_id": "DRV-001", "pref": "scenic"}).status_code == 422
    assert client.post("/api/v1/messages", json={"driver_id": "DRV-001", "text": ""}).status_code == 422


def test_dispatch_in_sql(client: TestClient) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.db.models import Base
    from app.repositories.dispatch import DispatchStore

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    store = DispatchStore(sessionmaker(bind=engine, expire_on_commit=False))
    store.add_message("DRV-001", text="first")
    store.set_plan("DRV-001", "greenest")
    store.mark_read("DRV-001")
    snap = store.snapshot("DRV-001")
    assert snap["plans"] == {"DRV-001": "greenest"}
    assert [(m["text"], m["pref"], m["read"]) for m in snap["messages"]] == [(None, "greenest", True), ("first", None, True)]
    engine.dispose()


def test_delivery_advances_trip_and_is_logged(client: TestClient) -> None:
    trip = next(t for t in client.get("/api/v1/trips").json() if t["id"] == "TRP-002")
    done = trip["parcels_delivered"]
    r = client.post("/api/v1/trips/TRP-002/deliver", json={"pref": "greenest", "co2_saved_kg": 0.07})
    assert r.status_code == 200
    assert r.json()["parcels_delivered"] == done + 1
    after = next(t for t in client.get("/api/v1/trips").json() if t["id"] == "TRP-002")
    assert after["parcels_delivered"] == done + 1
    logged = client.get("/api/v1/dispatch", params={"driver_id": "DRV-002"}).json()["deliveries"]
    assert [(d["trip_id"], d["parcel"], d["pref"], d["co2_saved_kg"]) for d in logged] == [("TRP-002", done + 1, "greenest", 0.07)]


def test_last_parcel_completes_trip_and_more_are_refused(client: TestClient) -> None:
    trip = next(t for t in client.get("/api/v1/trips").json() if t["id"] == "TRP-001")
    for _ in range(trip["parcels_total"] - trip["parcels_delivered"]):
        last = client.post("/api/v1/trips/TRP-001/deliver", json={})
    assert last.json()["status"] == "completed"
    assert client.post("/api/v1/trips/TRP-001/deliver", json={}).status_code == 409
    assert client.post("/api/v1/trips/TRP-999/deliver", json={}).status_code == 404
