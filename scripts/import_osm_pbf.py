"""Import a clipped OpenStreetMap PBF road network into project-local SQLite."""

import argparse
from pathlib import Path

from app.services.osm_network import DEFAULT_BBOX, DEFAULT_ROAD_DATABASE, import_osm_pbf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pbf",
        type=Path,
        required=True,
        help="Path to the source .osm.pbf file (the source file is read only).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ROAD_DATABASE,
        help="SQLite output path (default: data/road_network.sqlite).",
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        default=DEFAULT_BBOX,
        help="Area to import; defaults to a bounded Kolkata/Howrah/New Town region.",
    )
    args = parser.parse_args()
    counts = import_osm_pbf(args.pbf, args.output, tuple(args.bbox))
    print(
        f"Imported {counts['nodes']} road nodes and "
        f"{counts['directed_edges']} directed road segments to {args.output}."
    )
    print("Travel-time routing uses OSM posted/default speeds, not live traffic.")
    print("Fuel and CO2 values are not calculated until ML models are integrated.")


if __name__ == "__main__":
    main()
