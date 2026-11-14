"""Tests for SQL-backed fleet record storage using SQLite."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, DriverRecord
from app.db.mysql import _seed_empty_database
from app.repositories.store import FleetStore


def test_sql_store_reads_seeded_fleet_records() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    store = FleetStore(sessions)

    _seed_empty_database(sessions)

    assert store.mode == "mysql"
    assert len(store.list_records("drivers")) == 7
    assert len(store.list_records("trucks")) == 8
    assert len(store.list_records("trips")) == 5

    engine.dispose()


def test_sql_store_does_not_seed_partially_populated_database() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    store = FleetStore(sessions)
    with sessions.begin() as session:
        session.add(
            DriverRecord(
                id="existing-driver",
                name="Existing Driver",
                phone="000",
                licence_number="EXISTING",
                experience_years=1,
                rating=4.0,
                status="off_duty",
            )
        )

    _seed_empty_database(sessions)

    assert len(store.list_records("drivers")) == 1
    assert store.list_records("trucks") == []
    assert store.list_records("trips") == []

    engine.dispose()
