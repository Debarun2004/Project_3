"""MySQL connection and initial fleet-data setup."""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import URL, create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.db.models import Base, DriverRecord, TripRecord, TruckRecord
from app.repositories.store import DATA_DIRECTORY, FleetStore

MODEL_BY_COLLECTION = {
    "drivers": DriverRecord,
    "trucks": TruckRecord,
    "trips": TripRecord,
}


def _read_demo_records(collection: str) -> list[dict[str, Any]]:
    path: Path = DATA_DIRECTORY / f"{collection}.json"
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _model_record(collection: str, record: dict[str, Any]) -> dict[str, Any]:
    if collection == "trucks" and "Payload" in record:
        model_record = {
            key: value for key, value in record.items() if key != "Payload"
        }
        model_record["payload_kg"] = record["Payload"]
        return model_record
    return record.copy()


def _seed_empty_database(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        counts = {
            model: session.scalar(select(func.count()).select_from(model)) or 0
            for model in MODEL_BY_COLLECTION.values()
        }
        if any(counts.values()):
            return
        for collection, model in MODEL_BY_COLLECTION.items():
            session.add_all(
                model(**_model_record(collection, record))
                for record in _read_demo_records(collection)
            )


def connect_mysql(settings: Settings) -> tuple[FleetStore, Engine]:
    """Connect to MySQL, create app tables, and seed only a wholly empty fleet."""
    url = URL.create(
        "mysql+pymysql",
        username=settings.mysql_user,
        password=settings.mysql_password,
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        query={"charset": "utf8mb4"},
    )
    engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        Base.metadata.create_all(engine)
        if settings.mysql_seed_demo_data:
            _seed_empty_database(sessions)
    except SQLAlchemyError as error:
        engine.dispose()
        raise RuntimeError(
            "Could not initialize MySQL. Check that the database exists, "
            "the service is running, and MYSQL_HOST, MYSQL_PORT, MYSQL_USER, "
            "and MYSQL_PASSWORD are correct. No credentials are shown."
        ) from error
    return FleetStore(sessions), engine
