"""SQLAlchemy models for fleet data stored in MySQL."""

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for application database models."""


class DriverRecord(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    licence_number: Mapped[str] = mapped_column(String(64), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    truck_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    route_name: Mapped[str | None] = mapped_column(String(120), nullable=True)


class TruckRecord(Base):
    __tablename__ = "trucks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    registration_number: Mapped[str] = mapped_column(String(64), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_kg: Mapped[float] = mapped_column("Payload", Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    driver_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    route_name: Mapped[str | None] = mapped_column(String(120), nullable=True)


class TripRecord(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    driver_id: Mapped[str] = mapped_column(String(64), nullable=False)
    truck_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(160), nullable=False)
    destination: Mapped[str] = mapped_column(String(160), nullable=False)
    route_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    parcels_total: Mapped[int] = mapped_column(Integer, nullable=False)
    parcels_delivered: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_travel_time_minutes: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    estimated_fuel_consumption_liters: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    estimated_co2_emissions_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_mock_estimate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
