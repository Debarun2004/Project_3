"""Tests for preserving truck values while renaming the capacity column."""

import pytest
from sqlalchemy import create_engine, inspect, text

from scripts.migrate_truck_payload import rename_truck_payload_column


def test_renames_capacity_column_and_preserves_values() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE trucks "
                "(id TEXT PRIMARY KEY, capacity_kg REAL NOT NULL)"
            )
        )
        connection.execute(
            text("INSERT INTO trucks (id, capacity_kg) VALUES ('truck-1', 5000)")
        )

    assert rename_truck_payload_column(engine) is True
    columns = {column["name"] for column in inspect(engine).get_columns("trucks")}
    with engine.connect() as connection:
        value = connection.execute(
            text('SELECT "Payload" FROM trucks WHERE id = \'truck-1\'')
        ).scalar_one()

    assert "Payload" in columns
    assert "capacity_kg" not in columns
    assert value == 5000
    assert rename_truck_payload_column(engine) is False
    engine.dispose()


def test_migration_reports_ambiguous_column_state() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text(
                'CREATE TABLE trucks (id TEXT PRIMARY KEY, capacity_kg REAL, "Payload" REAL)'
            )
        )

    with pytest.raises(RuntimeError, match="Both"):
        rename_truck_payload_column(engine)

    engine.dispose()
