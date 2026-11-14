"""Driver data access."""

from typing import Any

from app.repositories.store import FleetStore
from app.schemas.fleet import Driver, DriverCreate


def list_drivers(store: FleetStore) -> list[Driver]:
    return [Driver.model_validate(record) for record in store.list_records("drivers")]


def create_driver(store: FleetStore, driver: DriverCreate) -> Driver:
    record: dict[str, Any] = store.create_record(
        "drivers", driver.model_dump(mode="json")
    )
    return Driver.model_validate(record)
