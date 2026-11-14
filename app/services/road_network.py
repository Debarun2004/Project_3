"""Build a directed road graph from validated, already-loaded edge records."""

from collections.abc import Iterable, Mapping
import math
from typing import Any

import networkx as nx

EDGE_METRICS = (
    "length_km",
    "travel_time_minutes",
    "fuel_consumption_liters",
    "co2_emissions_kg",
)


def build_road_graph(
    edges: Iterable[Mapping[str, Any]],
) -> nx.MultiDiGraph:
    """Create a directed graph from edge records without loading external data.

    Every edge must include a source, destination, and non-negative numeric
    values for distance, travel time, fuel, and CO2 supplied by upstream
    services. This function does not estimate missing metrics.
    """
    graph = nx.MultiDiGraph()

    for row_number, edge in enumerate(edges, start=1):
        missing = {"source_node", "target_node", *EDGE_METRICS} - edge.keys()
        if missing:
            raise ValueError(
                f"Edge record {row_number} is missing: {', '.join(sorted(missing))}"
            )

        source = edge["source_node"]
        target = edge["target_node"]
        if source is None or target is None:
            raise ValueError(f"Edge record {row_number} has a null endpoint")

        metrics: dict[str, float] = {}
        for field in EDGE_METRICS:
            try:
                value = float(edge[field])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Edge record {row_number} has invalid {field}"
                ) from error
            if not math.isfinite(value) or value < 0:
                raise ValueError(
                    f"Edge record {row_number} has invalid {field}; "
                    "expected a finite, non-negative number"
                )
            metrics[field] = value

        graph.add_edge(source, target, **metrics)

    if graph.number_of_edges() == 0:
        raise ValueError("Cannot build a road graph from an empty edge collection")

    return graph
