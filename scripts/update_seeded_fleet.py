"""Refresh only the original placeholder fleet rows in the configured database."""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, select, update

from app.core.config import get_settings
from app.db.models import DriverRecord, TripRecord, TruckRecord
from app.db.mysql import connect_mysql

DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "demo"
MODEL_BY_COLLECTION = {
    "drivers": (DriverRecord, "driver-demo-"),
    "trucks": (TruckRecord, "truck-demo-"),
    "trips": (TripRecord, "trip-demo-"),
}
ID_PREFIXES = {
    "driver-demo-001": "DRV-001",
    "driver-demo-002": "DRV-002",
    "driver-demo-003": "DRV-003",
    "driver-demo-004": "DRV-004",
    "driver-demo-005": "DRV-005",
    "driver-demo-006": "DRV-006",
    "driver-demo-007": "DRV-007",
    "truck-demo-001": "TRK-001",
    "truck-demo-002": "TRK-002",
    "truck-demo-003": "TRK-003",
    "truck-demo-004": "TRK-004",
    "truck-demo-005": "TRK-005",
    "truck-demo-006": "TRK-006",
    "truck-demo-007": "TRK-007",
    "truck-demo-008": "TRK-008",
    "trip-demo-001": "TRP-001",
    "trip-demo-002": "TRP-002",
    "trip-demo-003": "TRP-003",
    "trip-demo-004": "TRP-004",
    "trip-demo-005": "TRP-005",
}


def _read_records(collection: str) -> list[dict[str, Any]]:
    with (DATA_DIRECTORY / f"{collection}.json").open(encoding="utf-8") as file:
        return json.load(file)


def update_seeded_fleet(engine: Engine) -> dict[str, int]:
    """Rename/update known placeholder rows while preserving user-created rows."""
    updates: list[tuple[Any, str, dict[str, Any]]] = []
    for collection, (model, old_prefix) in MODEL_BY_COLLECTION.items():
        for record in _read_records(collection):
            new_id = record["id"]
            suffix = new_id.rsplit("-", 1)[1]
            old_id = f"{old_prefix}{suffix}"
            updates.append((model, old_id, record))

    updated = {name: 0 for name in MODEL_BY_COLLECTION}
    with engine.begin() as connection:
        for model, old_id, record in updates:
            old_exists = connection.scalar(
                select(model.id).where(model.id == old_id)
            )
            new_exists = connection.scalar(
                select(model.id).where(model.id == record["id"])
            )
            if old_exists and new_exists:
                raise RuntimeError(
                    f"Cannot update {old_id}: target ID {record['id']} already exists."
                )

        for old_id, new_id in ID_PREFIXES.items():
            if old_id.startswith("truck-demo-"):
                connection.execute(
                    update(DriverRecord)
                    .where(DriverRecord.truck_id == old_id)
                    .values(truck_id=new_id)
                )
                connection.execute(
                    update(TripRecord)
                    .where(TripRecord.truck_id == old_id)
                    .values(truck_id=new_id)
                )
            elif old_id.startswith("driver-demo-"):
                connection.execute(
                    update(TruckRecord)
                    .where(TruckRecord.driver_id == old_id)
                    .values(driver_id=new_id)
                )
                connection.execute(
                    update(TripRecord)
                    .where(TripRecord.driver_id == old_id)
                    .values(driver_id=new_id)
                )

        for collection, (model, _) in MODEL_BY_COLLECTION.items():
            for record in _read_records(collection):
                suffix = record["id"].rsplit("-", 1)[1]
                old_id = f"{MODEL_BY_COLLECTION[collection][1]}{suffix}"
                model_values = record.copy()
                if collection == "trucks":
                    model_values["payload_kg"] = model_values.pop("Payload")
                result = connection.execute(
                    update(model)
                    .where(model.id == old_id)
                    .values(**model_values)
                )
                updated[collection] += result.rowcount or 0
    return updated


def main() -> None:
    store, engine = connect_mysql(get_settings())
    try:
        if store.mode != "mysql":
            raise RuntimeError("The configured data source is not MySQL.")
        counts = update_seeded_fleet(engine)
        total = sum(counts.values())
        print(f"Updated {total} original sample records in MySQL: {counts}")
        print("Other records were left unchanged.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
