"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import API_VERSION, APP_NAME, get_settings
from app.db.mysql import connect_mysql
from app.repositories.store import FleetStore


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Connect to the configured data source for the application lifetime."""
    settings = get_settings()
    engine = None
    if settings.data_source == "mysql":
        application.state.fleet_store, engine = connect_mysql(settings)
    else:
        application.state.fleet_store = FleetStore()
    try:
        yield
    finally:
        if engine is not None:
            engine.dispose()


app = FastAPI(
    title=APP_NAME,
    description=(
        "Backend API for Dynamic Route-Optimization & CO₂ Footprint "
        "Estimator for Fleet Logistics."
    ),
    version=API_VERSION,
    lifespan=lifespan,
)
app.include_router(api_router)
