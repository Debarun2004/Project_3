import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split

# Set styling
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Load data and prepare test split (same split used during training)
df_gt = pd.read_csv("training_ground_truth.csv")
df_traffic = pd.read_csv("traffic_dynamics.csv")
df_vehicles = pd.read_csv("vehicles_fleet.csv")
df_roads = pd.read_csv("west_bengal_roads.csv")

df_merged = pd.merge(df_gt, df_traffic, on=["edge_id", "timestamp"], how="inner")
df_merged = pd.merge(df_merged, df_vehicles, on="vehicle_id", how="inner")
df_merged = pd.merge(df_merged, df_roads, on="edge_id", how="inner")

categorical_cols = ['road_type', 'surface_type', 'city', 'terrain_type', 'vehicle_type', 'day_type']
df_merged = pd.get_dummies(df_merged, columns=[col for col in categorical_cols if col in df_merged.columns], drop_first=True)

exclude_cols = [
    'trip_id', 'edge_id', 'vehicle_id', 'timestamp', 'source_node', 'target_node', 
    'target_travel_time_sec', 'target_fuel_consumption_liters', 'target_co2_emissions_g'
]

X = df_merged.select_dtypes(include=[np.number]).drop(columns=[col for col in exclude_cols if col in df_merged.columns], errors='ignore')

# 1. Travel Time Plot
y_time = df_merged['target_travel_time_sec']
_, X_test, _, y_time_test = train_test_split(X, y_time, test_size=0.2, random_state=42)
time_model = joblib.load("xgboost_travel_time_model.pkl")
y_time_pred = time_model.predict(X_test)

sns.scatterplot(x=y_time_test, y=y_time_pred, ax=axes[0], alpha=0.3, color="blue")
axes[0].plot([y_time_test.min(), y_time_test.max()], [y_time_test.min(), y_time_test.max()], 'r--', lw=2)
axes[0].set_title("Travel Time Prediction")
axes[0].set_xlabel("Actual (seconds)")
axes[0].set_ylabel("Predicted (seconds)")

# 2. Fuel Consumption Plot
y_fuel = df_merged['target_fuel_consumption_liters']
_, _, _, y_fuel_test = train_test_split(X, y_fuel, test_size=0.2, random_state=42)
fuel_model = joblib.load("xgboost_fuel_model.pkl")
y_fuel_pred = fuel_model.predict(X_test)

sns.scatterplot(x=y_fuel_test, y=y_fuel_pred, ax=axes[1], alpha=0.3, color="green")
axes[1].plot([y_fuel_test.min(), y_fuel_test.max()], [y_fuel_test.min(), y_fuel_test.max()], 'r--', lw=2)
axes[1].set_title("Fuel Prediction")
axes[1].set_xlabel("Actual (liters)")
axes[1].set_ylabel("Predicted (liters)")

# 3. CO2 Emissions Plot
y_co2 = df_merged['target_co2_emissions_g']
_, _, _, y_co2_test = train_test_split(X, y_co2, test_size=0.2, random_state=42)
co2_model = joblib.load("xgboost_co2_model.pkl")
y_co2_pred = co2_model.predict(X_test)

sns.scatterplot(x=y_co2_test, y=y_co2_pred, ax=axes[2], alpha=0.3, color="purple")
axes[2].plot([y_co2_test.min(), y_co2_test.max()], [y_co2_test.min(), y_co2_test.max()], 'r--', lw=2)
axes[2].set_title("CO2 Prediction")
axes[2].set_xlabel("Actual (grams)")
axes[2].set_ylabel("Predicted (grams)")

plt.tight_layout()
plt.savefig("model_performance_graphs.png", dpi=300)
print("Graphs generated and saved as 'model_performance_graphs.png'!")
plt.show()