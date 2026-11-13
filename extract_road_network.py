import csv
import math
import numpy as np
import osmium
import pandas as pd
import requests

PBF_PATH = "eastern-zone-261022.osm.pbf"
NODES_CSV = "nodes.csv"
EDGES_CSV = "west_bengal_roads.csv"

# Bounding boxes for logistics study zones: [min_lon, min_lat, max_lon, max_lat]
ZONES = {
    "Urban": {"bbox": (88.2, 22.4, 88.4, 22.7), "city": "Kolkata/Howrah"},
    "Industrial": {"bbox": (87.1, 23.4, 87.4, 23.6), "city": "Durgapur/Asansol"},
    "Rural": {"bbox": (86.8, 23.1, 87.2, 23.4), "city": "Bankura/Purulia"},
    "Hilly": {"bbox": (88.1, 26.9, 88.6, 27.2), "city": "Darjeeling/Kalimpong"},
}

DEFAULTS = {
    "motorway": {"lanes": "4", "max_speed": "100", "surface_type": "asphalt"},
    "trunk": {"lanes": "4", "max_speed": "80", "surface_type": "asphalt"},
    "primary": {"lanes": "2", "max_speed": "60", "surface_type": "asphalt"},
    "secondary": {"lanes": "2", "max_speed": "50", "surface_type": "asphalt"},
    "tertiary": {"lanes": "2", "max_speed": "40", "surface_type": "paved"},
    "residential": {"lanes": "1", "max_speed": "30", "surface_type": "paved"},
    "unclassified": {"lanes": "1", "max_speed": "30", "surface_type": "unpaved"},
}


def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def get_terrain_and_city(lon, lat):
    for zone, info in ZONES.items():
        b = info["bbox"]
        if b[0] <= lon <= b[2] and b[1] <= lat <= b[3]:
            return zone, info["city"]
    return None, None


class ZoneFilteredNetworkHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()
        self.nodes_dict = {}
        self.edges = []

    def way(self, w):
        if "highway" not in w.tags:
            return

        road_type = w.tags["highway"]
        if road_type in [
            "footway",
            "pedestrian",
            "steps",
            "cycleway",
            "path",
            "service",
        ]:
            return

        default_vals = DEFAULTS.get(
            road_type,
            {"lanes": "1", "max_speed": "30", "surface_type": "unclassified"},
        )

        lanes = w.tags.get("lanes", default_vals["lanes"])
        maxspeed = w.tags.get("maxspeed", default_vals["max_speed"])
        surface = w.tags.get("surface", default_vals["surface_type"])

        nodes = [n for n in w.nodes]

        for i in range(len(nodes) - 1):
            src_node, tgt_node = nodes[i], nodes[i + 1]

            try:
                lon1, lat1 = src_node.location.lon, src_node.location.lat
                lon2, lat2 = tgt_node.location.lon, tgt_node.location.lat

                terrain_type, city = get_terrain_and_city(lon1, lat1)
                if terrain_type is None:
                    continue

                self.nodes_dict[src_node.ref] = (lat1, lon1)
                self.nodes_dict[tgt_node.ref] = (lat2, lon2)

                length_in_km = haversine_km(lon1, lat1, lon2, lat2)

                self.edges.append(
                    {
                        "edge_id": f"{w.id}_{i}",
                        "source_node": src_node.ref,
                        "target_node": tgt_node.ref,
                        "road_type": road_type,
                        "length_in_km": round(length_in_km, 4),
                        "lanes": lanes,
                        "max_speed": maxspeed,
                        "surface_type": surface,
                        "city": city,
                        "terrain_type": terrain_type,
                    }
                )
            except osmium.InvalidLocationError:
                continue


# 1. Parse PBF file directly
print("Parsing PBF file for study zones...")
handler = ZoneFilteredNetworkHandler()
handler.apply_file(PBF_PATH, locations=True)

print(f"Extracted {len(handler.nodes_dict)} zone nodes.")
print(f"Extracted {len(handler.edges)} zone road segments.")

# 2. Export nodes.csv via lightweight standard python file stream
print(f"Saving {NODES_CSV}...")
with open(NODES_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["node_id", "lat", "lon"])
    for node_id, (lat, lon) in handler.nodes_dict.items():
        writer.writerow([node_id, lat, lon])

# 3. Create DataFrame for filtered edges
edges_df = pd.DataFrame(handler.edges)

edges_df["lanes"] = (
    pd.to_numeric(
        edges_df["lanes"].astype(str).str.extract(r"(\d+)")[0], errors="coerce"
    )
    .fillna(1)
    .astype(int)
)

edges_df["max_speed"] = (
    pd.to_numeric(
        edges_df["max_speed"].astype(str).str.extract(r"(\d+)")[0],
        errors="coerce",
    )
    .fillna(30)
    .astype(int)
)


# 4. Fetch elevation and calculate gradients
def fetch_elevations(locations_list, batch_size=100):
    url = "https://api.open-elevation.com/api/v1/lookup"
    elevations = []

    for i in range(0, len(locations_list), batch_size):
        batch = locations_list[i : i + batch_size]
        try:
            res = requests.post(url, json={"locations": batch}, timeout=10)
            if res.status_code == 200:
                elevations.extend(
                    [r["elevation"] for r in res.json()["results"]]
                )
            else:
                elevations.extend([0.0] * len(batch))
        except Exception:
            elevations.extend([0.0] * len(batch))

    return elevations


print("Fetching elevations for node locations...")
source_coords = [
    {
        "latitude": handler.nodes_dict[src][0],
        "longitude": handler.nodes_dict[src][1],
    }
    for src in edges_df["source_node"]
]
target_coords = [
    {
        "latitude": handler.nodes_dict[tgt][0],
        "longitude": handler.nodes_dict[tgt][1],
    }
    for tgt in edges_df["target_node"]
]

edges_df["source_elevation"] = fetch_elevations(source_coords)
edges_df["target_elevation"] = fetch_elevations(target_coords)

# Gradient calculation
length_m = edges_df["length_in_km"] * 1000.0
edges_df["gradient"] = np.where(
    length_m > 0,
    (
        (edges_df["target_elevation"] - edges_df["source_elevation"])
        / length_m
    )
    * 100.0,
    0.0,
).round(2)

edges_df["absolute_gradient"] = edges_df["gradient"].abs()

# Save final clean CSV
edges_df.drop(
    columns=["source_elevation", "target_elevation"],
    inplace=True,
    errors="ignore",
)
edges_df.to_csv(EDGES_CSV, index=False)

print(
    f"Successfully generated {NODES_CSV} and {EDGES_CSV} without database dependencies!"
)