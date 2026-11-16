"""Control-room messages to drivers and the route option assigned to each driver."""

from fastapi import APIRouter, HTTPException, Request, status

from app.repositories.drivers import list_drivers
from app.schemas.dispatch import Dispatch, MarkRead, Message, MessageCreate, PlanSet

router = APIRouter(prefix="/api/v1", tags=["dispatch"])


def _known_driver(request: Request, driver_id: str) -> None:
    if not any(d.id == driver_id for d in list_drivers(request.app.state.fleet_store)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown driver: {driver_id}")


@router.get("/dispatch", response_model=Dispatch)
def get_dispatch(request: Request, driver_id: str | None = None) -> Dispatch:
    """Every message and plan, or only one driver's when `driver_id` is given."""
    return Dispatch(**request.app.state.dispatch.snapshot(driver_id))


@router.post("/messages", response_model=Message, status_code=status.HTTP_201_CREATED)
def post_message(body: MessageCreate, request: Request) -> Message:
    _known_driver(request, body.driver_id)
    return Message(**request.app.state.dispatch.add_message(body.driver_id, text=body.text.strip()))


@router.post("/messages/read", status_code=status.HTTP_204_NO_CONTENT)
def post_read(body: MarkRead, request: Request) -> None:
    request.app.state.dispatch.mark_read(body.driver_id)


@router.post("/plans", response_model=Message, status_code=status.HTTP_201_CREATED)
def post_plan(body: PlanSet, request: Request) -> Message:
    """Assign a route option; the driver also gets a message saying so."""
    _known_driver(request, body.driver_id)
    return Message(**request.app.state.dispatch.set_plan(body.driver_id, body.pref))
