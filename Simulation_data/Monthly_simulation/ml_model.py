import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import os
import random

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# -------- SETTINGS --------
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulation_data")

if not os.path.exists(BASE_DIR):
    print(f"❌ Simulation data folder not found: {BASE_DIR}")
    print("   Run main.py first to generate simulation data.")
    exit(1)

# Find all available tower CSV files
available_towers = []
for file in os.listdir(BASE_DIR):
    if file.startswith("tower_") and file.endswith("_month_data.csv"):
        tower_id = int(file.split("_")[1])
        available_towers.append(tower_id)

available_towers = sorted(available_towers)

if len(available_towers) < 10:
    print(f"❌ Not enough towers. Found {len(available_towers)} towers, need at least 10.")
    print(f"   Available towers: {available_towers}")
    exit(1)

print(f"📊 Found {len(available_towers)} towers: {available_towers}")

# Randomly select 5 for training, then 5 for testing from remaining
random.seed(42)
train_towers = random.sample(available_towers, 5)
remaining_towers = [t for t in available_towers if t not in train_towers]
test_towers = random.sample(remaining_towers, 5)

print(f"🏋️ Training towers: {train_towers}")
print(f"🧪 Testing towers: {test_towers} (5 randomly selected from remaining)")

# -------- LOAD AND PREPARE TRAINING DATA --------
train_data = []

for tower_id in train_towers:
    file_name = os.path.join(BASE_DIR, f"tower_{tower_id}_month_data.csv")
    
    if not os.path.exists(file_name):
        print(f"❌ Training file not found: {file_name}")
        continue
    
    df = pd.read_csv(file_name)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["hour"] = df["datetime"].dt.hour + df["datetime"].dt.minute / 60
    df["prev_soc"] = df["battery_soc_percent"].shift(1)
    df["soc_drop"] = df["prev_soc"] - df["battery_soc_percent"]
    df = df.dropna().reset_index(drop=True)
    
    train_data.append(df)

if not train_data:
    print("❌ No training data loaded!")
    exit(1)

train_df = pd.concat(train_data, ignore_index=True)

# -------- HANDLE COLUMN VARIANTS --------
user_col = "active_users" if "active_users" in train_df.columns else "effective_users"

if "tx_power_W" in train_df.columns:
    power_col = "tx_power_W"
elif "rf_power" in train_df.columns:
    power_col = "rf_power"
else:
    raise Exception("No power column found!")

# -------- FEATURES --------
X_full = train_df[[
    "prev_soc",
    "hour",
    "temperature_degC",
    user_col,
    "coverage_load",
    power_col
]]

y_full = train_df["soc_drop"]

# -------- TRAIN MODEL ON ALL TRAINING DATA --------
print(f"\n🔧 Training LinearRegression ONCE on combined data from {len(train_towers)} towers...")
print(f"   Training samples: {len(train_df)} total (from {len(train_towers)} towers)")
model = LinearRegression()
model.fit(X_full, y_full)

print(f"✅ Model trained ONCE. R² score: {model.score(X_full, y_full):.4f}")
print(f"   This single model will be tested on {len(test_towers)} selected towers")

# -------- CALCULATE CONFIDENCE INTERVAL FROM TRAINING RESIDUALS --------
train_pred = model.predict(X_full)
residuals = y_full - train_pred
std_error = np.std(residuals)
print(f"📊 Training residual std error: {std_error:.4f}")

# -------- TEST ON SELECTED TOWERS --------
print(f"\n🧪 Testing the SAME trained model on {len(test_towers)} selected towers...")

for test_tower_id in test_towers:
    file_name = os.path.join(BASE_DIR, f"tower_{test_tower_id}_month_data.csv")
    
    if not os.path.exists(file_name):
        print(f"❌ Test file not found: {file_name}")
        continue
    
    print(f"\n📈 Testing SAME model on Tower {test_tower_id}...")
    
    df_test = pd.read_csv(file_name)
    df_test["datetime"] = pd.to_datetime(df_test["datetime"])
    df_test["hour"] = df_test["datetime"].dt.hour + df_test["datetime"].dt.minute / 60
    df_test["prev_soc"] = df_test["battery_soc_percent"].shift(1)
    df_test["soc_drop"] = df_test["prev_soc"] - df_test["battery_soc_percent"]
    df_test = df_test.dropna().reset_index(drop=True)
    
    X_test = df_test[[
        "prev_soc",
        "hour",
        "temperature_degC",
        user_col,
        "coverage_load",
        power_col
    ]]
    
    # -------- PREDICT DROP --------
    drop_pred = model.predict(X_test)
    
    # -------- RECONSTRUCT SOC --------
    prev_soc_test = X_test["prev_soc"].values
    soc_pred = prev_soc_test - drop_pred
    soc_pred = np.minimum(soc_pred, prev_soc_test)
    
    # -------- CONFIDENCE INTERVALS --------
    upper_drop = drop_pred + 2 * std_error
    lower_drop = drop_pred - 2 * std_error
    
    upper_soc = prev_soc_test - lower_drop
    lower_soc = prev_soc_test - upper_drop
    
    upper_soc = np.minimum(upper_soc, prev_soc_test)
    lower_soc = np.minimum(lower_soc, prev_soc_test)
    lower_soc = np.maximum(lower_soc, 0)
    
    # -------- ACTUAL --------
    actual_soc = df_test["battery_soc_percent"].values
    
    # -------- METRICS --------
    mae = np.mean(np.abs(actual_soc - soc_pred))
    rmse = np.sqrt(np.mean((actual_soc - soc_pred) ** 2))
    
    print(f"  MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    # -------- PLOT --------
    plt.figure(figsize=(12, 6))
    
    plt.plot(actual_soc, label="Actual SOC", linewidth=2, color='blue')
    plt.plot(soc_pred, label="Predicted SOC", linewidth=2, color='orange')
    
    plt.fill_between(
        range(len(soc_pred)),
        lower_soc,
        upper_soc,
        alpha=0.3,
        color='orange',
        label=f"95% Confidence Interval (±2σ={std_error:.4f})"
    )
    
    plt.title(f"Tower {test_tower_id} Battery Prediction (Trained on Towers {train_towers})")
    plt.xlabel("Time Step")
    plt.ylabel("SOC (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_path = os.path.join(
        BASE_DIR,
        f"tower_{test_tower_id}_prediction_trained_on_{train_towers[0]}_et_al.png"
    )
    
    plt.savefig(plot_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved plot: {plot_path}")

print("\n🎉 CROSS-TOWER TESTING COMPLETED!")
