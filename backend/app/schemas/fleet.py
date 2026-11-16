"""Schemas for demo fleet, driver, and trip records."""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class DriverCreate(BaseModel):
    """Validated fields for creating a driver."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(pattern=r"^\d{10}$")
    licence_number: str = Field(min_length=1, max_length=64)
    experience_years: int = Field(ge=0)
    rating: float = Field(default=0, ge=0, le=5)
    status: Literal["on_duty", "off_duty"] = "off_duty"
    truck_id: str | None = None
    route_name: str | None = None


class Driver(DriverCreate):
    """Driver roster record with generated identifier."""

    id: str


class TruckCreate(BaseModel):
    """Validated fields for creating a truck."""

    model_config = ConfigDict(extra="forbid")

    registration_number: str = Field(min_length=1, max_length=64)
    vehicle_type: str = Field(min_length=1, max_length=64)
    payload_kg: float = Field(
        alias="Payload",
        validation_alias=AliasChoices("Payload", "payload_kg"),
        serialization_alias="Payload",
        gt=0,
    )
    status: Literal["on_road", "garage", "idle"] = "garage"
    driver_id: str | None = None
    route_name: str | None = None


class Truck(TruckCreate):
    """Fleet vehicle record with generated identifier."""

    id: str


class TripCreate(BaseModel):
    """Validated fields for creating a trip."""

    model_config = ConfigDict(extra="forbid")

    driver_id: str = Field(min_length=1, max_length=64)
    truck_id: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1, max_length=160)
    destination: str = Field(min_length=1, max_length=160)
    route_name: str = Field(min_length=1, max_length=120)
    status: Literal["planned", "in_progress", "completed", "cancelled"] = "planned"
    parcels_total: int = Field(ge=0)
    parcels_delivered: int = Field(default=0, ge=0)
    estimated_travel_time_minutes: float | None = Field(default=None, ge=0)
    estimated_fuel_consumption_liters: float | None = Field(default=None, ge=0)
    estimated_co2_emissions_kg: float | None = Field(default=None, ge=0)
    is_mock_estimate: bool = True

    @model_validator(mode="after")
    def delivered_does_not_exceed_total(self) -> "TripCreate":
        if self.parcels_delivered > self.parcels_total:
            raise ValueError("parcels_delivered cannot exceed parcels_total")
        return self


class Trip(TripCreate):
    """Trip progress record with generated identifier."""

    id: str


class DashboardSummary(BaseModel):
    """Aggregate fleet counters for the control-room overview."""

    drivers_total: int
    drivers_on_duty: int
    trucks_total: int
    trucks_in_garage: int
    trucks_on_road: int
    trips_in_progress: int
    trips_completed: int
