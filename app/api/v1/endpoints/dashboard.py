"""Fleet dashboard endpoints."""

from fastapi import APIRouter, Request

from app.schemas.fleet import DashboardSummary
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(request: Request) -> DashboardSummary:
    return get_dashboard_summary(request.app.state.fleet_store)
