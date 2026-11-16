"""Tests for safely refreshing the original seeded fleet rows."""

import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models import Base, DriverRecord, TripRecord, TruckRecord
from scripts.update_seeded_fleet import update_seeded_fleet

DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "demo"


def _insert_old_seed_records(session: Session) -> None:
    for collection, model, old_prefix in (
        ("drivers", DriverRecord, "driver-demo-"),
        ("trucks", TruckRecord, "truck-demo-"),
        ("trips", TripRecord, "trip-demo-"),
    ):
        records = json.loads(
            (DATA_DIRECTORY / f"{collection}.json").read_text(encoding="utf-8")
        )
        for record in records:
            seeded = record.copy()
            suffix = seeded["id"].rsplit("-", 1)[1]
            seeded["id"] = f"{old_prefix}{suffix}"
            if "driver_id" in seeded and seeded["driver_id"]:
                seeded["driver_id"] = f"driver-demo-{suffix}"
            if "truck_id" in seeded and seeded["truck_id"]:
                seeded["truck_id"] = f"truck-demo-{suffix}"
            if "truck_id" in seeded and collection == "drivers" and seeded["truck_id"]:
                seeded["truck_id"] = f"truck-demo-{suffix}"
            if collection == "trucks":
                seeded["payload_kg"] = seeded.pop("Payload")
            session.add(model(**seeded))


def test_refresh_updates_seed_rows_and_preserves_user_created_records() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        _insert_old_seed_records(session)
        session.add(
            DriverRecord(
                id="user-created-driver",
                name="Keep This Driver",
                phone="9000000999",
                licence_number="USER-LIC-001",
                experience_years=1,
                rating=4.0,
                status="off_duty",
            )
        )

    counts = update_seeded_fleet(engine)

    assert counts == {"drivers": 7, "trucks": 8, "trips": 7}
    with Session(engine) as session:
        assert session.get(DriverRecord, "DRV-001").name == "Aritra Sen"
        assert session.get(DriverRecord, "DRV-001").truck_id == "TRK-001"
        assert session.get(TruckRecord, "TRK-001").driver_id == "DRV-001"
        assert session.get(TripRecord, "TRP-001").driver_id == "DRV-001"
        assert session.get(TripRecord, "TRP-001").truck_id == "TRK-001"
        assert session.get(DriverRecord, "user-created-driver").name == "Keep This Driver"
        assert session.scalar(
            select(DriverRecord.id).where(DriverRecord.id == "driver-demo-001")
        ) is None

    engine.dispose()
