import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

print("Loading datasets...")
df_gt = pd.read_csv("training_ground_truth.csv")
df_traffic = pd.read_csv("traffic_dynamics.csv")
df_vehicles = pd.read_csv("vehicles_fleet.csv")
df_roads = pd.read_csv("west_bengal_roads.csv")

print("Merging datasets...")
df_merged = pd.merge(df_gt, df_traffic, on=["edge_id", "timestamp"], how="inner")
df_merged = pd.merge(df_merged, df_vehicles, on="vehicle_id", how="inner")
df_merged = pd.merge(df_merged, df_roads, on="edge_id", how="inner")

# Handle categorical columns using one-hot encoding
categorical_cols = ['road_type', 'surface_type', 'city', 'terrain_type', 'vehicle_type', 'day_type']
df_merged = pd.get_dummies(df_merged, columns=[col for col in categorical_cols if col in df_merged.columns], drop_first=True)

# Select numerical features for training (exclude IDs, timestamps, and target variables)
exclude_cols = [
    'trip_id', 'edge_id', 'vehicle_id', 'timestamp', 'source_node', 'target_node', 
    'target_travel_time_sec', 'target_fuel_consumption_liters', 'target_co2_emissions_g'
]

X = df_merged.select_dtypes(include=[np.number]).drop(
    columns=[col for col in exclude_cols if col in df_merged.columns], 
    errors='ignore'
)
# TARGET CHANGED TO CO2 EMISSIONS
y = df_merged['target_co2_emissions_g']

print(f"Feature matrix shape: {X.shape}")

# Train-test split (80-20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training XGBoost CO2 Prediction model...")
model = XGBRegressor(n_estimators=150, learning_rate=0.1, max_depth=6, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Predictions & Evaluation
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n--- Model 3: CO₂ Prediction Results ---")
print(f"MAE: {mae:.2f} grams")
print(f"RMSE: {rmse:.2f} grams")
print(f"R² Score: {r2:.4f}")
import joblib
joblib.dump(model, 'xgboost_co2_model.pkl')
print("Model saved successfully!")