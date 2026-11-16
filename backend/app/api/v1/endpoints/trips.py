"""Trip list endpoints."""

from fastapi import APIRouter, HTTPException, Request, status

from app.repositories.store import StoreNotWritableError
from app.repositories.trips import create_trip, list_trips
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
