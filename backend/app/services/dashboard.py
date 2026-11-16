"""Dashboard summary aggregation."""

from app.repositories.drivers import list_drivers
from app.repositories.store import FleetStore
from app.repositories.trips import list_trips
from app.repositories.trucks import list_trucks
from app.schemas.fleet import DashboardSummary


def get_dashboard_summary(store: FleetStore) -> DashboardSummary:
    drivers = list_drivers(store)
    trucks = list_trucks(store)
    trips = list_trips(store)
    return DashboardSummary(
        drivers_total=len(drivers),
        drivers_on_duty=sum(driver.status == "on_duty" for driver in drivers),
        trucks_total=len(trucks),
        trucks_in_garage=sum(truck.status == "garage" for truck in trucks),
        trucks_on_road=sum(truck.status == "on_road" for truck in trucks),
        trips_in_progress=sum(trip.status == "in_progress" for trip in trips),
        trips_completed=sum(trip.status == "completed" for trip in trips),
    )
