"""Reusable request and response schemas for route API operations."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VehicleType = Literal["truck", "van", "mini_truck"]
OptimizationPreference = Literal["fastest", "greenest", "balanced"]


class RouteRequestBase(BaseModel):
    """Validated locations and fleet inputs shared by route requests."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source: str = Field(min_length=1, description="Route origin")
    destination: str = Field(min_length=1, description="Route destination")
    vehicle_type: VehicleType
    payload_kg: float = Field(gt=0, allow_inf_nan=False)
    dispatch_time: datetime
    optimization_preference: OptimizationPreference

    @model_validator(mode="after")
    def validate_route_locations_and_time(self) -> "RouteRequestBase":
        if self.source.casefold() == self.destination.casefold():
            raise ValueError("source and destination must be different")
        if self.dispatch_time.utcoffset() is None:
            raise ValueError("dispatch_time must include timezone information")
        return self


class RouteComparisonRequest(RouteRequestBase):
    """Request for comparison of synthetic route options."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "Kolkata",
                "destination": "Howrah",
                "vehicle_type": "truck",
                "payload_kg": 500,
                "dispatch_time": "2026-11-06T10:00:00+05:30",
                "optimization_preference": "balanced",
            }
        }
    )


class RouteOptimizationRequest(RouteRequestBase):
    """Request for a synthetic route selected by optimization preference."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "Kolkata",
                "destination": "Howrah",
                "vehicle_type": "truck",
                "payload_kg": 500,
                "dispatch_time": "2026-11-06T10:00:00+05:30",
                "optimization_preference": "fastest",
            }
        }
    )


class NetworkRouteRequest(BaseModel):
    """Coordinates for routing on the imported static OSM road graph."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source: str = Field(min_length=1, max_length=160)
    destination: str = Field(min_length=1, max_length=160)
    source_latitude: float = Field(ge=-90, le=90)
    source_longitude: float = Field(ge=-180, le=180)
    destination_latitude: float = Field(ge=-90, le=90)
    destination_longitude: float = Field(ge=-180, le=180)
    preference: Literal["shortest", "fastest"] = "fastest"


class NetworkRouteResponse(BaseModel):
    """Static road-network route; no live traffic or ML metrics are implied."""

    is_mock: Literal[False] = False
    notice: str
    source: str
    destination: str
    preference: Literal["shortest", "fastest"]
    distance_km: float = Field(ge=0)
    posted_speed_travel_time_minutes: float = Field(ge=0)
    source_snap_distance_km: float = Field(ge=0)
    destination_snap_distance_km: float = Field(ge=0)
    fuel_consumption_liters: None = None
    co2_emissions_kg: None = None
    geometry: list[tuple[float, float]]


class RouteMetrics(BaseModel):
    """Route estimates with explicit, reusable metric units."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "estimated_distance_km": 12.0,
                "estimated_travel_time_minutes": 25.0,
                "estimated_fuel_consumption_liters": 2.0,
                "estimated_co2_emissions_kg": 5.0,
            }
        }
    )

    estimated_distance_km: float = Field(ge=0, allow_inf_nan=False)
    estimated_travel_time_minutes: float = Field(ge=0, allow_inf_nan=False)
    estimated_fuel_consumption_liters: float = Field(ge=0, allow_inf_nan=False)
    estimated_co2_emissions_kg: float = Field(ge=0, allow_inf_nan=False)


class HealthResponse(BaseModel):
    """API availability and integration readiness."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "application_name": "PrithibiRoute Backend API",
                "api_version": "1.0.0",
                "server_status": "ok",
                "ml_model_status": "not integrated",
                "dataset_status": "mysql",
            }
        }
    )

    application_name: str
    api_version: str
    server_status: Literal["ok"]
    ml_model_status: Literal["not integrated"]
    dataset_status: Literal["demo", "mysql"]


class RouteComparisonResponse(BaseModel):
    """Mock comparison output; metrics are not calculated estimates."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_mock": True,
                "notice": (
                    "Synthetic connectivity-test values only; not calculated "
                    "from road data or ML."
                ),
                "source": "Kolkata",
                "destination": "Howrah",
                "fastest_route": {
                    "estimated_distance_km": 12.0,
                    "estimated_travel_time_minutes": 25.0,
                    "estimated_fuel_consumption_liters": 2.0,
                    "estimated_co2_emissions_kg": 5.0,
                },
                "greenest_route": {
                    "estimated_distance_km": 14.0,
                    "estimated_travel_time_minutes": 32.0,
                    "estimated_fuel_consumption_liters": 1.8,
                    "estimated_co2_emissions_kg": 4.5,
                },
                "balanced_route": {
                    "estimated_distance_km": 13.0,
                    "estimated_travel_time_minutes": 28.0,
                    "estimated_fuel_consumption_liters": 1.9,
                    "estimated_co2_emissions_kg": 4.8,
                },
            }
        }
    )

    is_mock: Literal[True]
    notice: str
    source: str
    destination: str
    fastest_route: RouteMetrics
    greenest_route: RouteMetrics
    balanced_route: RouteMetrics


class RouteOptimizationResponse(BaseModel):
    """Mock preference-selected output; not a calculated optimized route."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_mock": True,
                "notice": (
                    "Synthetic connectivity-test values only; not calculated "
                    "from road data or ML."
                ),
                "source": "Kolkata",
                "destination": "Howrah",
                "selected_preference": "fastest",
                "optimized_route": {
                    "estimated_distance_km": 12.0,
                    "estimated_travel_time_minutes": 25.0,
                    "estimated_fuel_consumption_liters": 2.0,
                    "estimated_co2_emissions_kg": 5.0,
                },
            }
        }
    )

    is_mock: Literal[True]
    notice: str
    source: str
    destination: str
    selected_preference: OptimizationPreference
    optimized_route: RouteMetrics
