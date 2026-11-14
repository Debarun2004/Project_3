"""Rename the existing MySQL trucks.capacity_kg column to trucks.Payload."""

from sqlalchemy import URL, create_engine, inspect
from sqlalchemy.engine import Engine

from app.core.config import get_settings


def rename_truck_payload_column(engine: Engine) -> bool:
    """Rename capacity_kg without changing values; return whether it changed."""
    columns = {column["name"].casefold() for column in inspect(engine).get_columns("trucks")}
    if "capacity_kg" in columns and "payload" in columns:
        raise RuntimeError(
            "Both trucks.capacity_kg and trucks.Payload exist; "
            "review the table before migrating."
        )
    if "payload" in columns:
        return False
    if "capacity_kg" not in columns:
        raise RuntimeError(
            "Neither trucks.capacity_kg nor trucks.Payload exists."
        )

    preparer = engine.dialect.identifier_preparer
    table_name = preparer.quote("trucks")
    old_column = preparer.quote("capacity_kg")
    new_column = preparer.quote("Payload")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            f"ALTER TABLE {table_name} RENAME COLUMN {old_column} TO {new_column}"
        )
    return True


def main() -> None:
    settings = get_settings()
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
    try:
        changed = rename_truck_payload_column(engine)
        if changed:
            print("Renamed trucks.capacity_kg to trucks.Payload; values preserved.")
        else:
            print("trucks.Payload already exists; no migration needed.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
