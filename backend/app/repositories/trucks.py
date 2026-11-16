"""Truck data access."""

from typing import Any

from app.repositories.store import FleetStore
from app.schemas.fleet import Truck, TruckCreate


def list_trucks(store: FleetStore) -> list[Truck]:
    return [Truck.model_validate(record) for record in store.list_records("trucks")]


def create_truck(store: FleetStore, truck: TruckCreate) -> Truck:
    record: dict[str, Any] = store.create_record(
        "trucks", truck.model_dump(mode="json")
    )
    return Truck.model_validate(record)
