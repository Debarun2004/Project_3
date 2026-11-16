"""Health endpoint."""

from fastapi import APIRouter, Request

from app.core.config import API_VERSION, APP_NAME
from app.schemas.routes import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    """Report API health, service integrations, and data source mode."""
    return HealthResponse(
        application_name=APP_NAME,
        api_version=API_VERSION,
        server_status="ok",
        ml_model_status="not integrated",
        dataset_status=request.app.state.fleet_store.mode,
    )
