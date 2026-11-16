"""Import and query a direction-aware road graph from an OSM PBF file."""

import math
import heapq
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

import networkx as nx
import osmium

DEFAULT_BBOX = (88.15, 22.35, 88.65, 22.75)
DEFAULT_ROAD_DATABASE = (
    Path(__file__).resolve().parents[2] / "data" / "road_network.sqlite"
)
EXCLUDED_HIGHWAYS = {
    "bridleway",
    "construction",
    "cycleway",
    "footway",
    "pedestrian",
    "planned",
    "proposed",
    "steps",
}
EXCLUDED_ACCESS_VALUES = {"no", "private"}
DEFAULT_SPEED_KPH = {
    "motorway": 90,
    "motorway_link": 45,
    "trunk": 70,
    "trunk_link": 35,
    "primary": 50,
    "primary_link": 30,
    "secondary": 40,
    "secondary_link": 25,
    "tertiary": 35,
    "tertiary_link": 20,
    "unclassified": 25,
    "residential": 25,
    "living_street": 10,
    "service": 15,
    "track": 15,
}
EARTH_RADIUS_KM = 6371.0088


def _inside_bbox(lon: float, lat: float, bbox: tuple[float, float, float, float]) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def _parse_maxspeed(value: str | None, highway: str) -> float:
    if value:
        match = re.search(r"\d+(?:\.\d+)?", value)
        if match:
            speed = float(match.group())
            if "mph" in value.casefold():
                speed *= 1.609344
            if speed > 0:
                return speed
    return float(DEFAULT_SPEED_KPH.get(highway, 25))


def _is_routable_way(tags: Any) -> bool:
    highway = tags.get("highway")
    if not highway or highway in EXCLUDED_HIGHWAYS:
        return False
    if any(
        tags.get(key, "").casefold() in EXCLUDED_ACCESS_VALUES
        for key in ("access", "vehicle", "motor_vehicle", "motorcar", "hgv")
    ):
        return False
    return highway in DEFAULT_SPEED_KPH


def _oneway_direction(tags: Any) -> str:
    oneway = tags.get("oneway", "").casefold()
    if oneway in {"yes", "1", "true"}:
        return "forward"
    if oneway == "-1":
        return "reverse"
    if oneway in {"no", "0", "false"}:
        return "both"
    if tags.get("junction", "").casefold() in {"roundabout", "circular"}:
        return "forward"
    if tags.get("highway") == "motorway":
        return "forward"
    return "both"


def _haversine_km(
    first_lat: float,
    first_lon: float,
    second_lat: float,
    second_lon: float,
) -> float:
    lat1, lat2 = math.radians(first_lat), math.radians(second_lat)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(second_lon - first_lon)
    arc = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, arc)))


def import_osm_pbf(
    pbf_path: Path,
    database_path: Path = DEFAULT_ROAD_DATABASE,
    bbox: tuple[float, float, float, float] = DEFAULT_BBOX,
) -> dict[str, int]:
    """Extract public drivable OSM road segments in a bbox to a SQLite file."""
    if not pbf_path.is_file():
        raise FileNotFoundError(f"OSM PBF file not found: {pbf_path}")
    min_lon, min_lat, max_lon, max_lat = bbox
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError("Bounding box must be ordered min_lon,min_lat,max_lon,max_lat.")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path = database_path.with_suffix(database_path.suffix + ".tmp")
    if staging_path.exists():
        staging_path.unlink()
    connection = sqlite3.connect(staging_path)
    connection.executescript(
        """
        DROP TABLE IF EXISTS road_edges;
        DROP TABLE IF EXISTS road_nodes;
        CREATE TABLE road_nodes (
            node_id INTEGER PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        );
        CREATE TABLE road_edges (
            edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node INTEGER NOT NULL,
            target_node INTEGER NOT NULL,
            length_km REAL NOT NULL,
            speed_kph REAL NOT NULL,
            highway TEXT NOT NULL,
            way_id INTEGER NOT NULL
        );
        """
    )
    stats = {"nodes": 0, "directed_edges": 0}
    edge_batch: list[tuple[int, int, float, float, str, int]] = []
    node_batch: dict[int, tuple[int, float, float]] = {}

    class RoadHandler(osmium.SimpleHandler):
        def way(self, way: Any) -> None:
            if not _is_routable_way(way.tags):
                return
            located_nodes = []
            for node in way.nodes:
                try:
                    location = node.location
                    lon, lat = location.lon, location.lat
                except (osmium.InvalidLocationError, RuntimeError):
                    continue
                if _inside_bbox(lon, lat, bbox):
                    located_nodes.append((node.ref, lat, lon))
                else:
                    located_nodes.append(None)

            speed = _parse_maxspeed(way.tags.get("maxspeed"), way.tags["highway"])
            direction = _oneway_direction(way.tags)
            for first, second in zip(located_nodes, located_nodes[1:]):
                if first is None or second is None:
                    continue
                first_id, first_lat, first_lon = first
                second_id, second_lat, second_lon = second
                length_km = _haversine_km(
                    first_lat, first_lon, second_lat, second_lon
                )
                if length_km <= 0:
                    continue
                node_batch[first_id] = (first_id, first_lat, first_lon)
                node_batch[second_id] = (second_id, second_lat, second_lon)
                forward = (
                    first_id,
                    second_id,
                    length_km,
                    speed,
                    way.tags["highway"],
                    way.id,
                )
                reverse = (
                    second_id,
                    first_id,
                    length_km,
                    speed,
                    way.tags["highway"],
                    way.id,
                )
                if direction in {"forward", "both"}:
                    edge_batch.append(forward)
                if direction in {"reverse", "both"}:
                    edge_batch.append(reverse)

            if edge_batch and len(edge_batch) >= 5000:
                connection.executemany(
                    """
                    INSERT INTO road_edges
                        (source_node, target_node, length_km, speed_kph, highway, way_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    edge_batch,
                )
                connection.executemany(
                    """
                    INSERT OR REPLACE INTO road_nodes (node_id, latitude, longitude)
                    VALUES (?, ?, ?)
                    """,
                    node_batch.values(),
                )
                stats["directed_edges"] += len(edge_batch)
                edge_batch.clear()
                node_batch.clear()

    try:
        handler = RoadHandler()
        handler.apply_file(str(pbf_path), locations=True, idx="flex_mem")
        if edge_batch:
            connection.executemany(
                """
                INSERT INTO road_edges
                    (source_node, target_node, length_km, speed_kph, highway, way_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                edge_batch,
            )
            connection.executemany(
                """
                INSERT OR REPLACE INTO road_nodes (node_id, latitude, longitude)
                VALUES (?, ?, ?)
                """,
                node_batch.values(),
            )
            stats["directed_edges"] += len(edge_batch)
        stats["nodes"] = connection.execute(
            "SELECT COUNT(*) FROM road_nodes"
        ).fetchone()[0]
        if stats["directed_edges"] == 0:
            raise ValueError("No routable road segments found inside the bounding box.")
        connection.executescript(
            """
            CREATE INDEX road_edges_source_idx ON road_edges(source_node);
            CREATE INDEX road_edges_target_idx ON road_edges(target_node);
            CREATE INDEX road_nodes_coordinate_idx
                ON road_nodes(latitude, longitude);
            """
        )
        connection.commit()
    except Exception:
        connection.rollback()
        connection.close()
        if staging_path.exists():
            staging_path.unlink()
        raise
    finally:
        connection.close()

    try:
        staging_path.replace(database_path)
    except Exception:
        if staging_path.exists():
            staging_path.unlink()
        raise
    else:
        if staging_path.exists():
            staging_path.unlink()
    return stats


@lru_cache(maxsize=2)
def load_road_graph(database_path: str) -> nx.MultiDiGraph:
    """Load the imported road graph from SQLite and cache it per process."""
    path = Path(database_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Road graph is not imported yet: {path}. Run scripts.import_osm_pbf."
        )
    graph = nx.MultiDiGraph()
    with sqlite3.connect(path) as connection:
        for node_id, latitude, longitude in connection.execute(
            "SELECT node_id, latitude, longitude FROM road_nodes"
        ):
            graph.add_node(node_id, latitude=latitude, longitude=longitude)
        for source, target, length_km, speed_kph, highway in connection.execute(
            """
            SELECT source_node, target_node, length_km, speed_kph, highway
            FROM road_edges
            """
        ):
            graph.add_edge(
                source,
                target,
                length_km=length_km,
                speed_kph=speed_kph,
                highway=highway,
                travel_time_minutes=length_km / speed_kph * 60,
            )
    if graph.number_of_edges() == 0:
        raise ValueError(f"Road graph database contains no edges: {path}")
    return graph


def _nearest_node(
    graph: nx.MultiDiGraph, latitude: float, longitude: float
) -> tuple[int, float]:
    node_id, distance = min(
        (
            (
                node,
                _haversine_km(
                    latitude,
                    longitude,
                    attributes["latitude"],
                    attributes["longitude"],
                ),
            )
            for node, attributes in graph.nodes(data=True)
        ),
        key=lambda item: item[1],
    )
    if distance > 2:
        raise ValueError(
            f"Nearest mapped road is {distance:.2f} km away; "
            "choose a point closer to the imported road network."
        )
    return node_id, distance


def find_osm_route(
    graph: nx.MultiDiGraph,
    source_latitude: float,
    source_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
    preference: str,
) -> dict[str, Any]:
    """Find a static OSM route ranked by length or posted-speed travel time."""
    if preference not in {"shortest", "fastest"}:
        raise ValueError("OSM route preference must be 'shortest' or 'fastest'.")
    source, source_snap_km = _nearest_node(
        graph, source_latitude, source_longitude
    )
    destination, destination_snap_km = _nearest_node(
        graph, destination_latitude, destination_longitude
    )
    weight = "length_km" if preference == "shortest" else "travel_time_minutes"
    try:
        nodes = nx.shortest_path(graph, source, destination, weight=weight)
    except nx.NetworkXNoPath as error:
        raise ValueError("No directed road route exists between these coordinates.") from error

    distance_km = 0.0
    travel_time_minutes = 0.0
    for start, end in zip(nodes, nodes[1:]):
        edge = min(
            graph.get_edge_data(start, end).values(),
            key=lambda attributes: attributes[weight],
        )
        distance_km += edge["length_km"]
        travel_time_minutes += edge["travel_time_minutes"]
    geometry = [
        [
            graph.nodes[node]["latitude"],
            graph.nodes[node]["longitude"],
        ]
        for node in nodes
    ]
    return {
        "preference": preference,
        "source_node": source,
        "destination_node": destination,
        "source_snap_distance_km": source_snap_km,
        "destination_snap_distance_km": destination_snap_km,
        "distance_km": distance_km,
        "posted_speed_travel_time_minutes": travel_time_minutes,
        "geometry": geometry,
    }


def _snap_database_node(
    connection: sqlite3.Connection, latitude: float, longitude: float
) -> tuple[int, float]:
    latitude_radius = 2 / 110.574
    longitude_radius = 2 / (
        111.320 * max(math.cos(math.radians(latitude)), 0.01)
    )
    candidates = connection.execute(
        """
        SELECT node_id, latitude, longitude
        FROM road_nodes
        WHERE latitude BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
        """,
        (
            latitude - latitude_radius,
            latitude + latitude_radius,
            longitude - longitude_radius,
            longitude + longitude_radius,
        ),
    )
    nearest = min(
        (
            (
                node_id,
                _haversine_km(latitude, longitude, node_lat, node_lon),
            )
            for node_id, node_lat, node_lon in candidates
        ),
        key=lambda item: item[1],
        default=None,
    )
    if nearest is None or nearest[1] > 2:
        distance = "more than 2"
        if nearest is not None:
            distance = f"{nearest[1]:.2f}"
        raise ValueError(
            f"Nearest mapped road is {distance} km away; "
            "choose a point closer to the imported road network."
        )
    return nearest


def find_osm_route_in_database(
    database_path: Path,
    source_latitude: float,
    source_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
    preference: str,
) -> dict[str, Any]:
    """Find a route without loading the complete PBF graph into memory."""
    if preference not in {"shortest", "fastest"}:
        raise ValueError("OSM route preference must be 'shortest' or 'fastest'.")
    if not database_path.is_file():
        raise FileNotFoundError(
            f"Road graph is not imported yet: {database_path}. "
            "Run scripts.import_osm_pbf."
        )

    with sqlite3.connect(database_path) as connection:
        source, source_snap_km = _snap_database_node(
            connection, source_latitude, source_longitude
        )
        destination, destination_snap_km = _snap_database_node(
            connection, destination_latitude, destination_longitude
        )
        node_coordinates: dict[int, tuple[float, float]] = {}
        for node_id in (source, destination):
            node_coordinates[node_id] = connection.execute(
                "SELECT latitude, longitude FROM road_nodes WHERE node_id = ?",
                (node_id,),
            ).fetchone()
        if preference == "fastest":
            max_speed = connection.execute(
                "SELECT MAX(speed_kph) FROM road_edges"
            ).fetchone()[0]
            max_speed = max(float(max_speed or 1), 1)
        else:
            max_speed = 1.0

        def heuristic(node_id: int) -> float:
            coordinates = node_coordinates[node_id]
            destination_coordinates = node_coordinates[destination]
            straight_line_km = _haversine_km(
                coordinates[0],
                coordinates[1],
                destination_coordinates[0],
                destination_coordinates[1],
            )
            if preference == "fastest":
                return straight_line_km / max_speed
            return straight_line_km

        frontier: list[tuple[float, float, int]] = [
            (heuristic(source), 0.0, source)
        ]
        best_cost = {source: 0.0}
        previous: dict[int, tuple[int, float, float]] = {}
        adjacency_sql = f"""
            SELECT e.target_node, e.length_km, e.speed_kph,
                   n.latitude, n.longitude
            FROM road_edges AS e
            JOIN road_nodes AS n ON n.node_id = e.target_node
            WHERE e.source_node = ?
        """

        while frontier:
            _, cost, current = heapq.heappop(frontier)
            if cost != best_cost.get(current):
                continue
            if current == destination:
                break

            for neighbor, length_km, speed_kph, latitude, longitude in (
                connection.execute(adjacency_sql, (current,))
            ):
                node_coordinates[neighbor] = (latitude, longitude)
                edge_cost = (
                    length_km / speed_kph
                    if preference == "fastest"
                    else length_km
                )
                candidate_cost = cost + edge_cost
                if candidate_cost >= best_cost.get(neighbor, math.inf):
                    continue
                best_cost[neighbor] = candidate_cost
                previous[neighbor] = (current, length_km, speed_kph)
                heapq.heappush(
                    frontier,
                    (
                        candidate_cost + heuristic(neighbor),
                        candidate_cost,
                        neighbor,
                    ),
                )
        else:
            raise ValueError("No directed road route exists between these coordinates.")

        path_nodes = [destination]
        path_edges: list[tuple[float, float]] = []
        while path_nodes[-1] != source:
            parent, length_km, speed_kph = previous[path_nodes[-1]]
            path_edges.append((length_km, speed_kph))
            path_nodes.append(parent)
        path_nodes.reverse()
        path_edges.reverse()
        geometry = [node_coordinates[node] for node in path_nodes]

    return {
        "preference": preference,
        "source_node": source,
        "destination_node": destination,
        "source_snap_distance_km": source_snap_km,
        "destination_snap_distance_km": destination_snap_km,
        "distance_km": sum(length for length, _ in path_edges),
        "posted_speed_travel_time_minutes": sum(
            length / speed * 60 for length, speed in path_edges
        ),
        "geometry": geometry,
    }
