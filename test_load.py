import pandas as pd

# Load the core datasets in your folder
df_ground_truth = pd.read_csv("training_ground_truth.csv")
df_traffic = pd.read_csv("traffic_dynamics.csv")
df_vehicles = pd.read_csv("vehicles_fleet.csv")

# Print shapes and columns to check everything loaded properly
print("--- Ground Truth ---")
print(df_ground_truth.shape)
print(df_ground_truth.columns.tolist())

print("\n--- Traffic Dynamics ---")
print(df_traffic.shape)
print(df_traffic.columns.tolist())

print("\n--- Vehicles Fleet ---")
print(df_vehicles.shape)
print(df_vehicles.columns.tolist())