"""Trip list endpoints."""

from fastapi import APIRouter, HTTPException, Request, status

from app.repositories.store import StoreNotWritableError
from app.repositories.trips import create_trip, list_trips
from app.schemas.dispatch import DeliveryCreate
from app.schemas.fleet import Trip, TripCreate

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])


@router.get("", response_model=list[Trip])
def get_trips(request: Request) -> list[Trip]:
    return list_trips(request.app.state.fleet_store)


@router.post("", response_model=Trip, status_code=status.HTTP_201_CREATED)
def post_trip(trip: TripCreate, request: Request) -> Trip:
    try:
        return create_trip(request.app.state.fleet_store, trip)
    except StoreNotWritableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("/{trip_id}/deliver", response_model=Trip)
def post_delivery(trip_id: str, body: DeliveryCreate, request: Request) -> Trip:
    """Mark the trip's next parcel delivered and log it, with its route option and CO₂ saved, for the control room."""
    try:
        trip = request.app.state.fleet_store.deliver_parcel(trip_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown trip: {trip_id}")
    request.app.state.dispatch.add_delivery(
        trip_id, trip["driver_id"], trip["parcels_delivered"], body.pref, round(body.co2_saved_kg, 3)
    )
    return Trip.model_validate(trip)
