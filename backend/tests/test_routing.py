"""Tests for graph routing using a tiny synthetic graph fixture."""

import pytest

from app.services.road_network import build_road_graph
from app.services.routing import find_routes


@pytest.fixture
def sample_graph():
    return build_road_graph(
        [
            {
                "source_node": "A",
                "target_node": "B",
                "length_km": 2,
                "travel_time_minutes": 2,
                "fuel_consumption_liters": 1.0,
                "co2_emissions_kg": 2.64,
            },
            {
                "source_node": "B",
                "target_node": "D",
                "length_km": 2,
                "travel_time_minutes": 2,
                "fuel_consumption_liters": 1.0,
                "co2_emissions_kg": 2.64,
            },
            {
                "source_node": "A",
                "target_node": "C",
                "length_km": 5,
                "travel_time_minutes": 8,
                "fuel_consumption_liters": 0.5,
                "co2_emissions_kg": 1.32,
            },
            {
                "source_node": "C",
                "target_node": "D",
                "length_km": 5,
                "travel_time_minutes": 8,
                "fuel_consumption_liters": 0.5,
                "co2_emissions_kg": 1.32,
            },
        ]
    )


def test_finds_fastest_and_greenest_paths(sample_graph) -> None:
    routes = find_routes(sample_graph, "A", "D")

    assert routes["fastest"].nodes == ("A", "B", "D")
    assert routes["fastest"].travel_time_minutes == 4
    assert routes["greenest"].nodes == ("A", "C", "D")
    assert routes["greenest"].co2_emissions_kg == pytest.approx(2.64)


def test_balanced_route_is_one_of_the_candidate_routes(sample_graph) -> None:
    routes = find_routes(sample_graph, "A", "D")

    assert routes["balanced"] in (routes["fastest"], routes["greenest"])


def test_missing_edge_metrics_are_rejected() -> None:
    with pytest.raises(ValueError, match="missing"):
        build_road_graph([{"source_node": "A", "target_node": "B"}])


def test_negative_edge_metrics_are_rejected() -> None:
    edge = {
        "source_node": "A",
        "target_node": "B",
        "length_km": -1,
        "travel_time_minutes": 1,
        "fuel_consumption_liters": 1,
        "co2_emissions_kg": 1,
    }

    with pytest.raises(ValueError, match="finite, non-negative"):
        build_road_graph([edge])


def test_unreachable_destination_is_reported(sample_graph) -> None:
    with pytest.raises(ValueError, match="No directed route"):
        find_routes(sample_graph, "D", "A")
