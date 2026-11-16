"""Trip data access."""

from typing import Any

from app.repositories.store import FleetStore
from app.schemas.fleet import Trip, TripCreate


def list_trips(store: FleetStore) -> list[Trip]:
    return [Trip.model_validate(record) for record in store.list_records("trips")]


def create_trip(store: FleetStore, trip: TripCreate) -> Trip:
    record: dict[str, Any] = store.create_record(
        "trips", trip.model_dump(mode="json")
    )
    return Trip.model_validate(record)
