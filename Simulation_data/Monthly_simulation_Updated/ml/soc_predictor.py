"""
SOC Predictor Module

Machine learning utilities for training and testing battery SOC prediction models.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import os
import random

from sklearn.linear_model import LinearRegression


def train_soc_predictor(data_dir, train_towers=None, random_seed=42):
    """
    Train a Linear Regression model for SOC drop prediction.

    If train_towers not specified, finds all available tower CSVs and selects 5 randomly.

    Args:
        data_dir: Directory containing tower_*_month_data.csv files
        train_towers: List of tower IDs to train on (default: auto-select 5)
        random_seed: Random seed for reproducibility

    Returns:
        Tuple of (model, train_towers, std_error)
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    # Find available towers if not specified
    if train_towers is None:
        available_towers = []
        for file in os.listdir(data_dir):
            if file.startswith("tower_") and file.endswith("_month_data.csv"):
                tower_id = int(file.split("_")[1])
                available_towers.append(tower_id)

        available_towers = sorted(available_towers)

        if len(available_towers) < 5:
            raise ValueError(
                f"Not enough towers to train. Found {len(available_towers)}, need at least 5."
            )

        train_towers = random.sample(available_towers, 5)

    print(f"🏋️ Training on towers: {train_towers}")

    # Load and prepare training data
    train_data = []

    for tower_id in train_towers:
        file_name = os.path.join(data_dir, f"tower_{tower_id}_month_data.csv")

        if not os.path.exists(file_name):
            print(f"⚠️ Training file not found: {file_name}")
            continue

        df = pd.read_csv(file_name)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df["hour"] = df["datetime"].dt.hour + df["datetime"].dt.minute / 60
        df["prev_soc"] = df["battery_soc_percent"].shift(1)
        df["soc_drop"] = df["prev_soc"] - df["battery_soc_percent"]
        df = df.dropna().reset_index(drop=True)

        train_data.append(df)

    if not train_data:
        raise ValueError("No training data loaded!")

    train_df = pd.concat(train_data, ignore_index=True)

    # Handle column variants
    user_col = "active_users" if "active_users" in train_df.columns else "effective_users"

    if "tx_power_W" in train_df.columns:
        power_col = "tx_power_W"
    elif "rf_power" in train_df.columns:
        power_col = "rf_power"
    else:
        raise ValueError("No power column found!")

    # Prepare features
    X_full = train_df[
        ["prev_soc", "hour", "temperature_degC", user_col, "coverage_load", power_col]
    ]

    y_full = train_df["soc_drop"]

    # Train model
    print(f"🔧 Training LinearRegression on {len(train_df)} samples from {len(train_towers)} towers...")
    model = LinearRegression()
    model.fit(X_full, y_full)

    # Calculate residuals for confidence intervals
    train_pred = model.predict(X_full)
    residuals = y_full - train_pred
    std_error = np.std(residuals)

    print(f"✅ Model trained. R² score: {model.score(X_full, y_full):.4f}")
    print(f"📊 Training residual std error: {std_error:.4f}")

    return model, train_towers, std_error


def test_soc_predictor(model, data_dir, test_towers, std_error, output_dir=None):
    """
    Test trained model on specified towers.

    Args:
        model: Trained LinearRegression model
        data_dir: Directory containing tower_*_month_data.csv files
        test_towers: List of tower IDs to test on
        std_error: Standard error from training
        output_dir: Output directory for plots (default: data_dir)

    Returns:
        Dict of test results with keys: tower_id, mae, rmse
    """
    if output_dir is None:
        output_dir = data_dir

    results = []

    for test_tower_id in test_towers:
        file_name = os.path.join(data_dir, f"tower_{test_tower_id}_month_data.csv")

        if not os.path.exists(file_name):
            print(f"⚠️ Test file not found: {file_name}")
            continue

        print(f"\n📈 Testing Tower {test_tower_id}...")

        df_test = pd.read_csv(file_name)
        df_test["datetime"] = pd.to_datetime(df_test["datetime"])
        df_test["hour"] = df_test["datetime"].dt.hour + df_test["datetime"].dt.minute / 60
        df_test["prev_soc"] = df_test["battery_soc_percent"].shift(1)
        df_test["soc_drop"] = df_test["prev_soc"] - df_test["battery_soc_percent"]
        df_test = df_test.dropna().reset_index(drop=True)

        # Handle column variants
        user_col = "active_users" if "active_users" in df_test.columns else "effective_users"
        power_col = "tx_power_W" if "tx_power_W" in df_test.columns else "rf_power"

        X_test = df_test[
            ["prev_soc", "hour", "temperature_degC", user_col, "coverage_load", power_col]
        ]

        # Predict drop
        drop_pred = model.predict(X_test)

        # Reconstruct SOC
        prev_soc_test = X_test["prev_soc"].values
        soc_pred = prev_soc_test - drop_pred
        soc_pred = np.minimum(soc_pred, prev_soc_test)

        # Confidence intervals
        upper_drop = drop_pred + 2 * std_error
        lower_drop = drop_pred - 2 * std_error

        upper_soc = prev_soc_test - lower_drop
        lower_soc = prev_soc_test - upper_drop

        upper_soc = np.minimum(upper_soc, prev_soc_test)
        lower_soc = np.minimum(lower_soc, prev_soc_test)
        lower_soc = np.maximum(lower_soc, 0)

        # Actual
        actual_soc = df_test["battery_soc_percent"].values

        # Metrics
        mae = np.mean(np.abs(actual_soc - soc_pred))
        rmse = np.sqrt(np.mean((actual_soc - soc_pred) ** 2))

        print(f"  MAE: {mae:.4f}, RMSE: {rmse:.4f}")

        # Plot
        plt.figure(figsize=(12, 6))

        plt.plot(actual_soc, label="Actual SOC", linewidth=2, color="blue")
        plt.plot(soc_pred, label="Predicted SOC", linewidth=2, color="orange")

        plt.fill_between(
            range(len(soc_pred)),
            lower_soc,
            upper_soc,
            alpha=0.3,
            color="orange",
            label=f"95% CI (±2σ={std_error:.4f})",
        )

        plt.title(f"Tower {test_tower_id} Battery Prediction")
        plt.xlabel("Time Step")
        plt.ylabel("SOC (%)")
        plt.legend()
        plt.grid(True, alpha=0.3)

        plot_path = os.path.join(output_dir, f"tower_{test_tower_id}_prediction_monthly.png")

        plt.savefig(plot_path, dpi=100, bbox_inches="tight")
        plt.close()

        print(f"✅ Saved plot: {plot_path}")

        results.append({"tower_id": test_tower_id, "mae": mae, "rmse": rmse})

    return results
