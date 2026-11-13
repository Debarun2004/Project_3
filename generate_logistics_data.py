import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ==========================================
# CONFIGURATION & REAL-WORLD CONSTANTS
# ==========================================
CITIES = {
    'Kolkata': {'type': 'urban_hub', 'lat': (22.5, 22.6), 'lon': (88.3, 88.4), 'elev': (2, 10)},
    'Howrah': {'type': 'urban_hub', 'lat': (22.55, 22.65), 'lon': (88.25, 88.33), 'elev': (2, 10)},
    'New Town': {'type': 'urban_hub', 'lat': (22.58, 22.62), 'lon': (88.45, 88.5), 'elev': (2, 10)},
    'Durgapur': {'type': 'industrial_corridor', 'lat': (23.45, 23.55), 'lon': (87.25, 87.35), 'elev': (60, 100)},
    'Asansol': {'type': 'industrial_corridor', 'lat': (23.65, 23.75), 'lon': (86.9, 87.05), 'elev': (80, 150)},
    'Bankura': {'type': 'rural_district', 'lat': (23.2, 23.3), 'lon': (87.0, 87.15), 'elev': (70, 200)},
    'Purulia': {'type': 'rural_district', 'lat': (23.25, 23.4), 'lon': (86.3, 86.45), 'elev': (150, 300)},
    'Darjeeling': {'type': 'hilly_region', 'lat': (26.95, 27.1), 'lon': (88.2, 88.3), 'elev': (1500, 2200)},
    'Kalimpong': {'type': 'hilly_region', 'lat': (27.0, 27.15), 'lon': (88.4, 88.55), 'elev': (1000, 1500)}
}

START_DATE = datetime(2026, 10, 1)
DAYS = 31

print("Starting Data Generation...")

# ==========================================
# 1. GENERATE nodes.csv (1,500 rows)
# ==========================================
print("Generating nodes.csv...")
nodes_data = []
for i in range(1500):
    # Distribute nodes: 50% Urban, 20% Industrial, 20% Rural, 10% Hilly
    rand_val = np.random.rand()
    if rand_val < 0.5: city = np.random.choice(['Kolkata', 'Howrah', 'New Town'])
    elif rand_val < 0.7: city = np.random.choice(['Durgapur', 'Asansol'])
    elif rand_val < 0.9: city = np.random.choice(['Bankura', 'Purulia'])
    else: city = np.random.choice(['Darjeeling', 'Kalimpong'])
    
    props = CITIES[city]
    nodes_data.append({
        'node_id': i,
        'lat': round(np.random.uniform(*props['lat']), 5),
        'lon': round(np.random.uniform(*props['lon']), 5),
        'elevation': round(np.random.uniform(*props['elev']), 1),
        'junction_type': np.random.choice(['signalized', 'roundabout', 'stop_sign', 'uncontrolled'], p=[0.4, 0.1, 0.2, 0.3]),
        'city_mapped': city # Temp column for edge generation
    })
df_nodes = pd.DataFrame(nodes_data)
df_nodes[['node_id', 'lat', 'lon', 'elevation', 'junction_type']].to_csv('nodes.csv', index=False)


# ==========================================
# 2. GENERATE west_bengal_roads.csv (3,500 rows)
# ==========================================
print("Generating west_bengal_roads.csv...")
edges_data = []
for i in range(3500):
    city = np.random.choice(list(CITIES.keys()))
    terrain = CITIES[city]['type']
    
    # Pick two random nodes from the same city for realism
    city_nodes = df_nodes[df_nodes['city_mapped'] == city]['node_id'].values
    if len(city_nodes) > 1:
        src, dst = np.random.choice(city_nodes, 2, replace=False)
    else:
        src, dst = 0, 1 # Fallback
        
    length = round(np.random.uniform(0.5, 15.0), 2)
    max_speed = np.random.choice([30, 40, 60, 80])
    
    # Realistic gradients
    if terrain == 'hilly_region':
        raw_gradient = np.random.uniform(-0.15, 0.15) # Up to 15% grade
    elif terrain == 'urban_hub':
        raw_gradient = np.random.uniform(-0.02, 0.02)
    else:
        raw_gradient = np.random.uniform(-0.05, 0.05)
        
    edges_data.append({
        'edge_id': i,
        'source_node': src,
        'target_node': dst,
        'road_type': np.random.choice(['highway', 'arterial', 'residential']),
        'length_in_km': length,
        'lanes': np.random.choice([2, 4, 6]),
        'max_speed': max_speed,
        'surface_type': np.random.choice(['asphalt', 'concrete', 'unpaved'], p=[0.7, 0.2, 0.1]),
        'gradient': round(raw_gradient, 4),
        'absolute_gradient': round(abs(raw_gradient), 4),
        'city': city,
        'terrain_type': terrain,
        'road_heading_deg': np.random.randint(0, 360)
    })
df_edges = pd.DataFrame(edges_data)
df_edges.to_csv('west_bengal_roads.csv', index=False)


# ==========================================
# 3. GENERATE vehicles_fleet.csv (500 rows)
# ==========================================
print("Generating vehicles_fleet.csv...")
fleet_data = []
for i in range(500):
    v_type = np.random.choice(['LCV', 'Medium_Duty_Truck', 'Heavy_Duty_Diesel', 'Electric_Van'], p=[0.3, 0.3, 0.3, 0.1])
    
    if v_type == 'LCV': mass, cap, engine, area, drag = 1500, 2000, 'Diesel', 3.5, 0.4
    elif v_type == 'Medium_Duty_Truck': mass, cap, engine, area, drag = 4000, 8000, 'Diesel', 6.0, 0.6
    elif v_type == 'Heavy_Duty_Diesel': mass, cap, engine, area, drag = 8000, 25000, 'Diesel', 8.5, 0.7
    else: mass, cap, engine, area, drag = 2000, 1500, 'EV', 3.5, 0.3
        
    fleet_data.append({
        'vehicle_id': f"V_{i:04d}",
        'vehicle_type': v_type,
        'empty_mass': mass,
        'payload_capacity': cap,
        'engine_type': engine,
        'frontal_area_m2': area,
        'drag_coefficient': drag
    })
df_fleet = pd.DataFrame(fleet_data)
df_fleet.to_csv('vehicles_fleet.csv', index=False)


# ==========================================
# 4. GENERATE weather_conditions.csv (6,696 rows)
# ==========================================
print("Generating weather_conditions.csv...")
weather_data = []
for city in CITIES.keys():
    for day in range(DAYS):
        for hour in range(24):
            dt = START_DATE + timedelta(days=day, hours=hour)
            rain = round(np.random.exponential(1.5) if np.random.rand() > 0.8 else 0.0, 2)
            wind = round(np.random.normal(5, 2), 1)
            wind = max(0, wind)
            weather_data.append({
                'city': city,
                'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'rainfall_cm': rain,
                'heavy_rainfall_flag': 1 if rain > 6.45 else 0,
                'wind_speed_ms': wind,
                'wind_direction_deg': np.random.randint(0, 360),
                'weather_severity_score': round(min((rain + wind)/20, 1.0), 3)
            })
df_weather = pd.DataFrame(weather_data)
df_weather.to_csv('weather_conditions.csv', index=False)


# ==========================================
# 5. GENERATE traffic_dynamics.csv (~2.6M rows)
# ==========================================
print("Generating traffic_dynamics.csv (Vectorized - Please wait a moment)...")
timestamps = pd.date_range(START_DATE, periods=DAYS*24, freq='h')
# Create a MultiIndex of Edge X Timestamps
multi_idx = pd.MultiIndex.from_product([df_edges['edge_id'], timestamps], names=['edge_id', 'timestamp'])
df_traffic = pd.DataFrame(index=multi_idx).reset_index()

# Map free flow speeds
edge_speed_map = df_edges.set_index('edge_id')['max_speed'].to_dict()
df_traffic['free_flow_speed'] = df_traffic['edge_id'].map(edge_speed_map)

# Extract hour and day
df_traffic['hour'] = df_traffic['timestamp'].dt.hour
df_traffic['day_of_week'] = df_traffic['timestamp'].dt.dayofweek
df_traffic['day_type'] = np.where(df_traffic['day_of_week'] >= 5, 'weekend', 'weekday')

# Vectorized Peak Hour Logic (8-10 AM, 5-8 PM)
df_traffic['peak_hour_flag'] = np.where(df_traffic['hour'].isin([8,9,17,18,19]), 1, 0)

# Simulate current speed (drops during peak hours)
noise = np.random.normal(0.9, 0.1, len(df_traffic))
peak_penalty = np.where(df_traffic['peak_hour_flag'] == 1, np.random.uniform(0.4, 0.7, len(df_traffic)), 1.0)
df_traffic['current_speed'] = (df_traffic['free_flow_speed'] * noise * peak_penalty).clip(5, 80)
df_traffic['current_speed'] = df_traffic['current_speed'].round(1)

# Calculations
df_traffic['congestion_index'] = (df_traffic['current_speed'] / df_traffic['free_flow_speed']).round(3)
df_traffic['delay_pct'] = (((df_traffic['free_flow_speed'] - df_traffic['current_speed']) / df_traffic['free_flow_speed']) * 100).round(2)
df_traffic['traffic_pressure'] = (df_traffic['congestion_index'] * df_traffic['delay_pct']).round(2)

# Drop helper columns and save
df_traffic = df_traffic.drop(columns=['hour', 'day_of_week'])
df_traffic.to_csv('traffic_dynamics.csv', index=False)


# ==========================================
# 6. GENERATE training_ground_truth.csv (250,000 rows)
# ==========================================
print("Generating training_ground_truth.csv...")
trips_data = []

# Pre-fetch arrays for fast random sampling
edge_ids = df_edges['edge_id'].values
vehicle_ids = df_fleet['vehicle_id'].values

for i in range(250000):
    edge_idx = np.random.choice(edge_ids)
    veh_idx = np.random.choice(vehicle_ids)
    
    # Get physical attributes
    edge = df_edges.iloc[edge_idx]
    veh = df_fleet[df_fleet['vehicle_id'] == veh_idx].iloc[0]
    
    # Generate random logistics state
    payload = round(np.random.uniform(0, veh['payload_capacity']), 1)
    gross_mass = veh['empty_mass'] + payload
    utilization = (payload / veh['payload_capacity']) * 100 if veh['payload_capacity'] > 0 else 0
    
    # Simulate weather and speed context for this specific trip instance
    current_speed = np.random.uniform(10, edge['max_speed'])
    wind_speed = np.random.uniform(0, 15)
    wind_dir = np.random.randint(0, 360)
    
    # Physics calculations
    headwind = round(wind_speed * np.cos(np.radians(edge['road_heading_deg'] - wind_dir)), 2)
    road_resist = round(edge['absolute_gradient'] * gross_mass * 9.81, 2)
    
    # Target 1: Travel time (Distance / Speed)
    time_sec = round((edge['length_in_km'] / current_speed) * 3600, 1)
    
    # Target 2 & 3: Physics-based fuel and CO2
    # Base consumption + gradient penalty + aerodynamic drag penalty
    base_fuel_rate_per_km = 0.15 if veh['engine_type'] == 'Diesel' else 0.0  
    grade_penalty = max(0, edge['gradient'] * gross_mass * 0.0005)
    aero_penalty = (0.5 * 1.225 * veh['frontal_area_m2'] * veh['drag_coefficient'] * ((current_speed/3.6)**2)) * 0.0001
    
    fuel_liters = round((base_fuel_rate_per_km + grade_penalty + aero_penalty) * edge['length_in_km'], 3)
    
    if veh['engine_type'] == 'EV':
        fuel_liters = 0.0
        co2_g = 0.0
    else:
        co2_g = round(fuel_liters * 2640, 1) # 2.64kg CO2 per liter of diesel
        
    dt = START_DATE + timedelta(days=np.random.randint(0, DAYS), hours=np.random.randint(0, 24))

    trips_data.append({
        'trip_id': f"TRP_{i:06d}",
        'edge_id': edge_idx,
        'vehicle_id': veh_idx,
        'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
        'payload': payload,
        'gross_mass': gross_mass,
        'payload_utilization': round(utilization, 1),
        'headwind': headwind,
        'road_resistance': road_resist,
        'target_travel_time_sec': time_sec,
        'target_fuel_consumption_liters': fuel_liters,
        'target_co2_emissions_g': co2_g
    })

df_trips = pd.DataFrame(trips_data)
df_trips.to_csv('training_ground_truth.csv', index=False)

print("SUCCESS! All 6 CSV files have been successfully generated in your directory.")