import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# -------- SETTINGS --------
NUM_TOWERS = 5

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

for tower_id in range(NUM_TOWERS):

    file_name = os.path.join(
        BASE_DIR,
        f"tower_{tower_id}_day_data.csv"
    )

    if not os.path.exists(file_name):
        print(f"❌ File not found: {file_name}")
        continue

    print(f"\n📊 Processing Tower {tower_id}...")

    # -------- LOAD DATA --------
    df = pd.read_csv(file_name)

    df["datetime"] = pd.to_datetime(df["datetime"])
    df["hour"] = df["datetime"].dt.hour + df["datetime"].dt.minute / 60

    # -------- TEMPORAL FEATURES --------
    df["prev_soc"] = df["battery_soc_percent"].shift(1)
    df["soc_drop"] = df["prev_soc"] - df["battery_soc_percent"]

    df = df.dropna().reset_index(drop=True)

    # -------- HANDLE COLUMN VARIANTS --------
    user_col = "active_users" if "active_users" in df.columns else "effective_users"

    if "tx_power_W" in df.columns:
        power_col = "tx_power_W"
    elif "rf_power" in df.columns:
        power_col = "rf_power"
    else:
        raise Exception("No power column found!")

    # -------- FEATURES --------
    X = df[[
        "prev_soc",
        "hour",
        "temperature_degC",
        user_col,
        "coverage_load",
        power_col
    ]]

    y = df["soc_drop"]

    # -------- TRAIN TEST SPLIT --------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    # -------- MODEL (LINEAR REGRESSION) --------
    model = LinearRegression()
    model.fit(X_train, y_train)

    # -------- PREDICT DROP --------
    drop_pred = model.predict(X_test)

    # -------- RECONSTRUCT SOC --------
    prev_soc_test = X_test["prev_soc"].values
    soc_pred = prev_soc_test - drop_pred

    # 🔥 PHYSICAL CONSTRAINT (NO INCREASE)
    soc_pred = np.minimum(soc_pred, prev_soc_test)

    # -------- CONFIDENCE INTERVAL (RESIDUAL-BASED) --------
    train_pred = model.predict(X_train)
    residuals = y_train - train_pred

    std_error = np.std(residuals)

    upper_drop = drop_pred + 2 * std_error
    lower_drop = drop_pred - 2 * std_error

    upper_soc = prev_soc_test - lower_drop
    lower_soc = prev_soc_test - upper_drop

    # Clamp again
    upper_soc = np.minimum(upper_soc, prev_soc_test)
    lower_soc = np.minimum(lower_soc, prev_soc_test)

    # -------- ACTUAL --------
    actual_soc = df.loc[X_test.index, "battery_soc_percent"].values

    # -------- PLOT --------
    plt.figure(figsize=(10, 6))

    plt.plot(actual_soc, label="Actual SOC", linewidth=2)
    plt.plot(soc_pred, label="Predicted SOC", linewidth=2)

    plt.fill_between(
        range(len(soc_pred)),
        lower_soc,
        upper_soc,
        alpha=0.3,
        label="Confidence Interval"
    )

    plt.title(f"Tower {tower_id} Battery Prediction (Linear Model)")
    plt.xlabel("Time Step")
    plt.ylabel("SOC (%)")
    plt.legend()

    plot_path = os.path.join(
        BASE_DIR,
        f"tower_{tower_id}_prediction_linear.png"
    )

    plt.savefig(plot_path)
    plt.close()

    print(f"✅ Saved plot: {plot_path}")

print("\n🎉 ALL TOWERS PROCESSED SUCCESSFULLY!")