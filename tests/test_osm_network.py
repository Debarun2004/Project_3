"""Tests for importing and routing over a small OSM PBF fixture."""

import osmium
import pytest
from fastapi.testclient import TestClient

from app.services.osm_network import (
    find_osm_route,
    find_osm_route_in_database,
    import_osm_pbf,
    load_road_graph,
)


def _write_test_pbf(path) -> None:
    locations = {
        1: (88.30, 22.58),
        2: (88.31, 22.58),
        3: (88.32, 22.58),
        4: (88.31, 22.59),
    }
    writer = osmium.SimpleWriter(str(path))
    for node_id, (longitude, latitude) in locations.items():
        writer.add_node(
            osmium.osm.mutable.Node(
                id=node_id,
                location=osmium.osm.Location(longitude, latitude),
            )
        )
    refs = [
        osmium.osm.NodeRef(osmium.osm.Location(*locations[node_id]), node_id)
        for node_id in (1, 2, 3)
    ]
    writer.add_way(
        osmium.osm.mutable.Way(
            id=100,
            nodes=refs,
            tags={"highway": "residential", "oneway": "yes", "maxspeed": "30"},
        )
    )
    writer.add_way(
        osmium.osm.mutable.Way(
            id=200,
            nodes=[
                osmium.osm.NodeRef(osmium.osm.Location(*locations[node_id]), node_id)
                for node_id in (1, 4, 3)
            ],
            tags={"highway": "residential", "maxspeed": "20"},
        )
    )
    writer.close()


def test_imported_pbf_preserves_oneways_and_routes(tmp_path) -> None:
    pbf_path = tmp_path / "roads.osm.pbf"
    database_path = tmp_path / "road_network.sqlite"
    _write_test_pbf(pbf_path)

    stats = import_osm_pbf(
        pbf_path,
        database_path,
        bbox=(88.2, 22.4, 88.4, 22.7),
    )
    graph = load_road_graph(str(database_path))

    assert stats["directed_edges"] == 6
    assert graph.has_edge(1, 2)
    assert not graph.has_edge(2, 1)
    assert graph.has_edge(1, 4)
    assert graph.has_edge(4, 1)

    route = find_osm_route_in_database(
        database_path, 22.58, 88.30, 22.58, 88.32, "fastest"
    )
    assert route["geometry"][0] == pytest.approx((22.58, 88.30))
    assert route["geometry"][-1] == pytest.approx((22.58, 88.32))
    assert route["distance_km"] > 0
    assert route["posted_speed_travel_time_minutes"] > 0


def test_imported_pbf_rejects_points_far_from_mapped_roads(tmp_path) -> None:
    pbf_path = tmp_path / "roads.osm.pbf"
    database_path = tmp_path / "road_network.sqlite"
    _write_test_pbf(pbf_path)
    import_osm_pbf(pbf_path, database_path, bbox=(88.2, 22.4, 88.4, 22.7))
    graph = load_road_graph(str(database_path))

    with pytest.raises(ValueError, match="Nearest mapped road"):
        find_osm_route_in_database(
            database_path, 23.0, 89.0, 22.58, 88.32, "fastest"
        )


def test_network_route_api_returns_static_route_without_ml_estimates(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.api.v1.endpoints.routes.find_osm_route_in_database",
        lambda *args: {
            "preference": "fastest",
            "distance_km": 1.0,
            "posted_speed_travel_time_minutes": 2.0,
            "source_snap_distance_km": 0.0,
            "destination_snap_distance_km": 0.0,
            "geometry": [(22.58, 88.30), (22.58, 88.31)],
        },
    )

    response = client.post(
        "/routes/network",
        json={
            "source": "Howrah",
            "destination": "New Town",
            "source_latitude": 22.58,
            "source_longitude": 88.30,
            "destination_latitude": 22.58,
            "destination_longitude": 88.31,
            "preference": "fastest",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["is_mock"] is False
    assert result["distance_km"] == 1
    assert result["fuel_consumption_liters"] is None
    assert result["co2_emissions_kg"] is None
    assert len(result["geometry"]) == 2
