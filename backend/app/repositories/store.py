"""Demo JSON or MySQL fleet data store."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import insert, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import DriverRecord, TripRecord, TruckRecord

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "demo"
COLLECTIONS = ("drivers", "trucks", "trips")
RECORD_MODELS = {
    "drivers": DriverRecord,
    "trucks": TruckRecord,
    "trips": TripRecord,
}


class StoreNotWritableError(RuntimeError):
    """Raised when a write is requested while using read-only demo data."""


class FleetStore:
    """Read and create fleet records using demo JSON or SQLAlchemy."""

    def __init__(self, sessions: sessionmaker[Session] | None = None) -> None:
        self._sessions = sessions
        self._demo_data: dict[str, list[dict[str, Any]]] = {}
        if sessions is None:
            for collection in COLLECTIONS:
                path = DATA_DIRECTORY / f"{collection}.json"
                with path.open(encoding="utf-8") as file:
                    self._demo_data[collection] = json.load(file)

    @property
    def sessions(self) -> sessionmaker[Session] | None:
        """The SQL session factory, or None when serving demo JSON."""
        return self._sessions

    @property
    def mode(self) -> str:
        return "mysql" if self._sessions is not None else "demo"

    def list_records(self, collection: str) -> list[dict[str, Any]]:
        if collection not in COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection}")
        if self._sessions is None:
            return [record.copy() for record in self._demo_data[collection]]
        model = RECORD_MODELS[collection]
        with self._sessions() as session:
            records = session.scalars(select(model)).all()
            return [
                {
                    attribute.key: getattr(record, attribute.key)
                    for attribute in model.__mapper__.column_attrs
                }
                for record in records
            ]

    def create_record(
        self, collection: str, record: Mapping[str, Any]
    ) -> dict[str, Any]:
        if collection not in COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection}")
        if self._sessions is None:
            raise StoreNotWritableError(
                "Creating records requires the MySQL data source."
            )

        model = RECORD_MODELS[collection]
        created = {"id": str(uuid4()), **record}
        with self._sessions.begin() as session:
            session.execute(insert(model).values(**created))
        return created
