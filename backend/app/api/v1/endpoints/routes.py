"""Route comparison and optimization endpoints (currently mock responses)."""

from typing import Literal

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.services.osm_network import (
    DEFAULT_ROAD_DATABASE,
    find_osm_route_in_database,
)
from app.schemas.routes import (
    NetworkRouteRequest,
    NetworkRouteResponse,
    RouteComparisonRequest,
    RouteComparisonResponse,
    RouteMetrics,
    RouteOptimizationRequest,
    RouteOptimizationResponse,
)

router = APIRouter(prefix="/routes", tags=["routes"])
OSM_NOTICE = (
    "Static OpenStreetMap route using posted or default road speeds. "
    "No live traffic, ML fuel prediction, or CO2 prediction is integrated yet."
)

MOCK_METRICS = {
    "fastest": RouteMetrics(
        estimated_distance_km=12.0,
        estimated_travel_time_minutes=25.0,
        estimated_fuel_consumption_liters=2.0,
        estimated_co2_emissions_kg=5.0,
    ),
    "greenest": RouteMetrics(
        estimated_distance_km=14.0,
        estimated_travel_time_minutes=32.0,
        estimated_fuel_consumption_liters=1.8,
        estimated_co2_emissions_kg=4.5,
    ),
    "balanced": RouteMetrics(
        estimated_distance_km=13.0,
        estimated_travel_time_minutes=28.0,
        estimated_fuel_consumption_liters=1.9,
        estimated_co2_emissions_kg=4.8,
    ),
}
MOCK_NOTICE = (
    "Synthetic connectivity-test values only; not calculated from road data or ML."
)
OPTIMIZE_RESPONSE_EXAMPLE = {
    "is_mock": True,
    "notice": MOCK_NOTICE,
    "source": "Kolkata",
    "destination": "Howrah",
    "selected_preference": "fastest",
    "optimized_route": MOCK_METRICS["fastest"].model_dump(),
}
COMPARE_RESPONSE_EXAMPLE = {
    "is_mock": True,
    "notice": MOCK_NOTICE,
    "source": "Kolkata",
    "destination": "Howrah",
    "fastest_route": MOCK_METRICS["fastest"].model_dump(),
    "greenest_route": MOCK_METRICS["greenest"].model_dump(),
    "balanced_route": MOCK_METRICS["balanced"].model_dump(),
}


def _route_metrics(
    preference: Literal["fastest", "greenest", "balanced"],
) -> RouteMetrics:
    return MOCK_METRICS[preference].model_copy()


@router.post(
    "/compare",
    response_model=RouteComparisonResponse,
    responses={
        200: {
            "content": {
                "application/json": {"example": COMPARE_RESPONSE_EXAMPLE}
            }
        }
    },
)
def compare_routes(request: RouteComparisonRequest) -> RouteComparisonResponse:
    """Return clearly identified synthetic values for API connectivity testing."""
    return RouteComparisonResponse(
        is_mock=True,
        notice=MOCK_NOTICE,
        source=request.source,
        destination=request.destination,
        fastest_route=_route_metrics("fastest"),
        greenest_route=_route_metrics("greenest"),
        balanced_route=_route_metrics("balanced"),
    )


@router.post(
    "/optimize",
    response_model=RouteOptimizationResponse,
    responses={
        200: {
            "content": {
                "application/json": {"example": OPTIMIZE_RESPONSE_EXAMPLE}
            }
        }
    },
)
def optimize_route(
    request: RouteOptimizationRequest,
) -> RouteOptimizationResponse:
    """Return synthetic values selected by preference, not a real optimization."""
    preference = request.optimization_preference
    return RouteOptimizationResponse(
        is_mock=True,
        notice=MOCK_NOTICE,
        source=request.source,
        destination=request.destination,
        selected_preference=preference,
        optimized_route=_route_metrics(preference),
    )


@router.post(
    "/network",
    response_model=NetworkRouteResponse,
    responses={
        503: {"description": "OSM road graph has not been imported."},
        422: {"description": "No directed route exists for these coordinates."},
    },
)
def route_on_osm_network(
    request: NetworkRouteRequest,
) -> NetworkRouteResponse:
    """Route coordinate inputs over the locally imported static OSM graph."""
    database_path = Path(
        os.getenv("OSM_ROAD_DATABASE", str(DEFAULT_ROAD_DATABASE))
    )
    try:
        route = find_osm_route_in_database(
            database_path,
            request.source_latitude,
            request.source_longitude,
            request.destination_latitude,
            request.destination_longitude,
            request.preference,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return NetworkRouteResponse(
        is_mock=False,
        notice=OSM_NOTICE,
        source=request.source,
        destination=request.destination,
        preference=route["preference"],
        distance_km=route["distance_km"],
        posted_speed_travel_time_minutes=route[
            "posted_speed_travel_time_minutes"
        ],
        source_snap_distance_km=route["source_snap_distance_km"],
        destination_snap_distance_km=route["destination_snap_distance_km"],
        fuel_consumption_liters=None,
        co2_emissions_kg=None,
        geometry=route["geometry"],
    )
