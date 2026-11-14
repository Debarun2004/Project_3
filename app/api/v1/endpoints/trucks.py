"""Truck fleet endpoints."""

from fastapi import APIRouter, HTTPException, Request, status

from app.repositories.store import StoreNotWritableError
from app.repositories.trucks import create_truck, list_trucks
from app.schemas.fleet import Truck, TruckCreate

router = APIRouter(prefix="/api/v1/trucks", tags=["trucks"])


@router.get("", response_model=list[Truck])
def get_trucks(request: Request) -> list[Truck]:
    return list_trucks(request.app.state.fleet_store)


@router.post("", response_model=Truck, status_code=status.HTTP_201_CREATED)
def post_truck(truck: TruckCreate, request: Request) -> Truck:
    try:
        return create_truck(request.app.state.fleet_store, truck)
    except StoreNotWritableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
