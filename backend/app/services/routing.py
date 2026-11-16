"""Route selection over a loaded road graph with explicit edge metrics."""

from dataclasses import dataclass
from typing import Literal

import networkx as nx

RoutePreference = Literal["fastest", "greenest", "balanced"]


@dataclass(frozen=True)
class RouteResult:
    """A selected graph path and totals in the API's documented units."""

    nodes: tuple[str | int, ...]
    distance_km: float
    travel_time_minutes: float
    fuel_consumption_liters: float
    co2_emissions_kg: float


def _route_for_weight(
    graph: nx.MultiDiGraph,
    source: str | int,
    destination: str | int,
    weight: str,
) -> RouteResult:
    if source not in graph:
        raise ValueError(f"Unknown source node: {source}")
    if destination not in graph:
        raise ValueError(f"Unknown destination node: {destination}")

    try:
        nodes = nx.shortest_path(graph, source, destination, weight=weight)
    except nx.NetworkXNoPath as error:
        raise ValueError(
            f"No directed route exists from {source} to {destination}"
        ) from error

    totals = {
        "length_km": 0.0,
        "travel_time_minutes": 0.0,
        "fuel_consumption_liters": 0.0,
        "co2_emissions_kg": 0.0,
    }

    for start, end in zip(nodes, nodes[1:]):
        parallel_edges = graph.get_edge_data(start, end)
        edge = min(
            parallel_edges.values(),
            key=lambda attributes: attributes[weight],
        )
        for metric in totals:
            totals[metric] += edge[metric]

    return RouteResult(
        nodes=tuple(nodes),
        distance_km=totals["length_km"],
        travel_time_minutes=totals["travel_time_minutes"],
        fuel_consumption_liters=totals["fuel_consumption_liters"],
        co2_emissions_kg=totals["co2_emissions_kg"],
    )


def _balanced_choice(fastest: RouteResult, greenest: RouteResult) -> RouteResult:
    """Choose the better normalized time/emissions tradeoff of two candidates."""
    time_span = greenest.travel_time_minutes - fastest.travel_time_minutes
    emissions_span = fastest.co2_emissions_kg - greenest.co2_emissions_kg

    def score(route: RouteResult) -> float:
        time_cost = (
            (route.travel_time_minutes - fastest.travel_time_minutes) / time_span
            if time_span > 0
            else 0.0
        )
        emissions_cost = (
            (route.co2_emissions_kg - greenest.co2_emissions_kg)
            / emissions_span
            if emissions_span > 0
            else 0.0
        )
        return (time_cost + emissions_cost) / 2

    return min((fastest, greenest), key=score)


def find_routes(
    graph: nx.MultiDiGraph,
    source: str | int,
    destination: str | int,
) -> dict[RoutePreference, RouteResult]:
    """Return fastest, greenest and balanced routes from a loaded graph.

    The balanced option chooses between the fastest and greenest candidates
    using normalized travel-time and CO2 costs. Fuel/CO2 values must be supplied
    by trusted data or the ML prediction service; they are never invented here.
    """
    fastest = _route_for_weight(
        graph, source, destination, "travel_time_minutes"
    )
    greenest = _route_for_weight(graph, source, destination, "co2_emissions_kg")
    return {
        "fastest": fastest,
        "greenest": greenest,
        "balanced": _balanced_choice(fastest, greenest),
    }
