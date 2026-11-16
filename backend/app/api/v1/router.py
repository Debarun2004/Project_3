"""API router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.dispatch import router as dispatch_router
from app.api.v1.endpoints.drivers import router as drivers_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.trips import router as trips_router
from app.api.v1.endpoints.trucks import router as trucks_router
from app.api.v1.endpoints.routes import router as routes_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(dashboard_router)
api_router.include_router(drivers_router)
api_router.include_router(trucks_router)
api_router.include_router(trips_router)
api_router.include_router(routes_router)
api_router.include_router(dispatch_router)
