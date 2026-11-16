"""Driver roster endpoints."""

from fastapi import APIRouter, HTTPException, Request, status

from app.repositories.drivers import create_driver, list_drivers
from app.repositories.store import StoreNotWritableError
from app.schemas.fleet import Driver, DriverCreate

router = APIRouter(prefix="/api/v1/drivers", tags=["drivers"])


@router.get("", response_model=list[Driver])
def get_drivers(request: Request) -> list[Driver]:
    return list_drivers(request.app.state.fleet_store)


@router.post("", response_model=Driver, status_code=status.HTTP_201_CREATED)
def post_driver(driver: DriverCreate, request: Request) -> Driver:
    try:
        return create_driver(request.app.state.fleet_store, driver)
    except StoreNotWritableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
