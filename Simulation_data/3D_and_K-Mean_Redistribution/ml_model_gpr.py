"""Train and test a battery SOC prediction model using Gaussian Process Regression.

This module loads saved tower CSV data, trains both Linear Regression and GPR models
on a set of towers, and evaluates trained models on a separate set with uncertainty 
quantification and comparative analysis.
"""

import os
import random
import sys
import warnings
warnings.filterwarnings('ignore')

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for file output
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel, Matern
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# -------- SETTINGS --------
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulation_data")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gpr_output")

# Create output directory if needed
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    print(f"ERROR: Not enough towers. Found {len(available_towers)} towers, need at least 10.")
    print(f"   Available towers: {available_towers}")
    exit(1)

print(f"Found {len(available_towers)} towers: {available_towers}")

# Randomly select 5 towers for training and 5 for testing
random.seed(42)
train_towers = random.sample(available_towers, 5)
remaining_towers = [t for t in available_towers if t not in train_towers]
test_towers = random.sample(remaining_towers, 5)

print(f"Training towers: {train_towers}")
print(f"Testing towers: {test_towers} (5 randomly selected from remaining)")

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

    # Remove unrealistic reset/recharge transitions that show as -100% drop
    valid_drop = (df["soc_drop"] > -10.0) & (df["soc_drop"] < 10.0)
    if len(df) - valid_drop.sum() > 0:
        print(f"   WARNING: Filtering {len(df) - valid_drop.sum()} abnormal SOC transitions from tower {tower_id}")
    df = df[valid_drop].reset_index(drop=True)
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

# -------- FEATURES AND TARGET --------
X_train = train_df[[
    "prev_soc",
    "hour",
    "temperature_degC",
    user_col,
    "coverage_load",
    power_col
]]
y_train = train_df["battery_soc_percent"]

print(f"\nTraining data prepared: {len(X_train)} samples, {X_train.shape[1]} features")

# -------- TRAIN LINEAR REGRESSION MODEL --------
print(f"\nTraining LinearRegression...")
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)
print(f"   LinearRegression trained")

# -------- TRAIN GAUSSIAN PROCESS REGRESSION MODEL --------
print(f"\nTraining Gaussian Process Regressor...")
print(f"   Using Matern kernel with RBF components for non-linear patterns...")

# Use a subset for GPR training to avoid O(n^2) memory blow-up
MAX_GPR_TRAIN_SAMPLES = 2500
if len(X_train) > MAX_GPR_TRAIN_SAMPLES:
    print(f"   WARNING: GPR will train on a subset of {MAX_GPR_TRAIN_SAMPLES} samples instead of {len(X_train)}")
    rng = np.random.RandomState(42)
    sample_idx = rng.choice(len(X_train), size=MAX_GPR_TRAIN_SAMPLES, replace=False)
    X_train_gpr = X_train.iloc[sample_idx]
    y_train_gpr = y_train.iloc[sample_idx]
else:
    X_train_gpr = X_train
    y_train_gpr = y_train

# Define kernel: Matern kernel captures non-smooth patterns better than RBF
# Combines constant, Matern, and white noise components
kernel = C(1.0, (1e-3, 1e3)) * Matern(length_scale=1.0, nu=2.5) + WhiteKernel(noise_level=0.1)

gpr_model = GaussianProcessRegressor(
    kernel=kernel,
    n_restarts_optimizer=3,
    alpha=1e-6,
    normalize_y=True,
    random_state=42
)

gpr_model.fit(X_train_gpr, y_train_gpr)
print(f"   Gaussian Process Regressor trained")
print(f"   Learned kernel: {gpr_model.kernel_}")

# -------- EVALUATE ON TEST DATA --------
print(f"\nEvaluating models on test data...\n")

test_results_all = []
model_performances = {"LinearRegression": {}, "GaussianProcess": {}}

for test_tower_id in test_towers:
    file_name = os.path.join(BASE_DIR, f"tower_{test_tower_id}_month_data.csv")
    
    if not os.path.exists(file_name):
        print(f"WARNING: Test file not found: {file_name}")
        continue
    
    df = pd.read_csv(file_name)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["hour"] = df["datetime"].dt.hour + df["datetime"].dt.minute / 60
    df["prev_soc"] = df["battery_soc_percent"].shift(1)
    df["soc_drop"] = df["prev_soc"] - df["battery_soc_percent"]
    df = df.dropna().reset_index(drop=True)

    valid_drop = (df["soc_drop"] > -10.0) & (df["soc_drop"] < 10.0)
    if len(df) - valid_drop.sum() > 0:
        print(f"   WARNING: Filtering {len(df) - valid_drop.sum()} abnormal SOC transitions from tower {test_tower_id}")
    df = df[valid_drop].reset_index(drop=True)
    
    X_test = df[[
        "prev_soc",
        "hour",
        "temperature_degC",
        user_col,
        "coverage_load",
        power_col
    ]]
    y_test = df["battery_soc_percent"]
    
    # Predictions from LinearRegression
    lr_pred = lr_model.predict(X_test)
    lr_mse = mean_squared_error(y_test, lr_pred)
    lr_rmse = np.sqrt(lr_mse)
    lr_mae = mean_absolute_error(y_test, lr_pred)
    lr_r2 = r2_score(y_test, lr_pred)
    
    # Predictions from GPR (with uncertainty)
    gpr_pred, gpr_std = gpr_model.predict(X_test, return_std=True)
    gpr_mse = mean_squared_error(y_test, gpr_pred)
    gpr_rmse = np.sqrt(gpr_mse)
    gpr_mae = mean_absolute_error(y_test, gpr_pred)
    gpr_r2 = r2_score(y_test, gpr_pred)
    
    actual_soc = df["battery_soc_percent"].values
    gpr_soc_pred = gpr_pred
    gpr_soc_pred = np.minimum(np.maximum(gpr_soc_pred, 0.0), 100.0)

    upper_soc = gpr_pred + 1.96 * gpr_std
    lower_soc = gpr_pred - 1.96 * gpr_std
    upper_soc = np.minimum(np.maximum(upper_soc, 0.0), 100.0)
    lower_soc = np.minimum(np.maximum(lower_soc, 0.0), 100.0)

    gpr_soc_mae = np.mean(np.abs(actual_soc - gpr_soc_pred))
    gpr_soc_rmse = np.sqrt(np.mean((actual_soc - gpr_soc_pred) ** 2))
    
    # Save a time-series SOC plot for this tower (limit to 2000 time steps)
    max_steps = min(2000, len(actual_soc))
    time_steps = np.arange(max_steps)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.fill_between(
        time_steps,
        lower_soc[:max_steps],
        upper_soc[:max_steps],
        alpha=0.25,
        color='gold',
        label="95% SOC Confidence Interval",
        zorder=1
    )
    ax.plot(time_steps, gpr_soc_pred[:max_steps], label="GPR Predicted SOC", color='orange', linewidth=2, linestyle='--', alpha=0.9, zorder=2)
    ax.plot(time_steps, actual_soc[:max_steps], label="Actual SOC", color='black', linewidth=3, alpha=0.9, zorder=3)
    ax.scatter(time_steps[::50], actual_soc[:max_steps:50], color='black', s=18, alpha=0.8, zorder=4)
    ax.set_title(f"Tower {test_tower_id} GPR SOC Time Series")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("SOC (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, f"tower_{test_tower_id}_gpr_soc_timeseries.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # Calculate how often actual values fall within 95% confidence interval
    confidence_lower = gpr_pred - 1.96 * gpr_std
    confidence_upper = gpr_pred + 1.96 * gpr_std
    within_ci = np.sum((y_test >= confidence_lower) & (y_test <= confidence_upper)) / len(y_test) * 100
    
    print(f"Tower {test_tower_id}:")
    print(f"  LinearRegression - RMSE: {lr_rmse:.4f}, MAE: {lr_mae:.4f}, R²: {lr_r2:.4f}")
    print(f"  GPR actual SOC - RMSE: {gpr_rmse:.4f}, MAE: {gpr_mae:.4f}, R²: {gpr_r2:.4f}")
    print(f"  GPR SOC series - RMSE: {gpr_soc_rmse:.4f}, MAE: {gpr_soc_mae:.4f}")
    print(f"  GPR Calibration - {within_ci:.1f}% of actual values within 95% CI")
    print(f"  Saved: tower_{test_tower_id}_gpr_soc_timeseries.png")
    print()
    
    test_results_all.append({
        "tower_id": test_tower_id,
        "lr_rmse": lr_rmse,
        "lr_mae": lr_mae,
        "lr_r2": lr_r2,
        "gpr_rmse": gpr_rmse,
        "gpr_mae": gpr_mae,
        "gpr_r2": gpr_r2,
        "gpr_soc_rmse": gpr_soc_rmse,
        "gpr_soc_mae": gpr_soc_mae,
        "gpr_calibration": within_ci,
        "y_test": y_test.values,
        "lr_pred": lr_pred,
        "gpr_pred": gpr_pred,
        "gpr_std": gpr_std,
        "actual_soc": actual_soc,
        "gpr_soc_pred": gpr_soc_pred,
        "gpr_soc_upper": upper_soc,
        "gpr_soc_lower": lower_soc
    })
    
    # Store for aggregated metrics
    for metric in ["rmse", "mae", "r2"]:
        if metric not in model_performances["LinearRegression"]:
            model_performances["LinearRegression"][metric] = []
            model_performances["GaussianProcess"][metric] = []
        
        model_performances["LinearRegression"][metric].append(
            lr_rmse if metric == "rmse" else (lr_mae if metric == "mae" else lr_r2)
        )
        model_performances["GaussianProcess"][metric].append(
            gpr_rmse if metric == "rmse" else (gpr_mae if metric == "mae" else gpr_r2)
        )

# -------- SUMMARY STATISTICS --------
print("\n" + "="*60)
print("AGGREGATE PERFORMANCE METRICS")
print("="*60)

for metric in ["rmse", "mae", "r2"]:
    lr_vals = model_performances["LinearRegression"][metric]
    gpr_vals = model_performances["GaussianProcess"][metric]
    
    print(f"\n{metric.upper()}:")
    print(f"  LinearRegression - Mean: {np.mean(lr_vals):.4f}, Std: {np.std(lr_vals):.4f}")
    print(f"  GPR              - Mean: {np.mean(gpr_vals):.4f}, Std: {np.std(gpr_vals):.4f}")
    
    improvement = ((np.mean(lr_vals) - np.mean(gpr_vals)) / np.mean(lr_vals) * 100) if metric != "r2" else ((np.mean(gpr_vals) - np.mean(lr_vals)) / abs(np.mean(lr_vals)) * 100)
    if metric == "r2":
        improvement = ((np.mean(gpr_vals) - np.mean(lr_vals)) / abs(np.mean(lr_vals)) * 100)
    print(f"  GPR Improvement: {improvement:.2f}%")

# -------- VISUALIZATIONS --------
print(f"\nCreating visualizations...")

# 1. Predictions vs Actual for first test tower
if test_results_all:
    result = test_results_all[0]
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # LinearRegression
    axes[0].scatter(result["lr_pred"], result["y_test"], alpha=0.5, label="Predictions")
    line_min = min(result["lr_pred"].min(), result["y_test"].min())
    line_max = max(result["lr_pred"].max(), result["y_test"].max())
    axes[0].plot([line_min, line_max], 
                 [line_min, line_max], 'r--', lw=2, label="Perfect Prediction")
    axes[0].set_xlabel("Predicted SOC (%)")
    axes[0].set_ylabel("Actual SOC (%)")
    axes[0].set_title(f"LinearRegression - Tower {result['tower_id']} (RMSE: {result['lr_rmse']:.4f})")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # GPR with uncertainty
    sorted_idx = np.argsort(result["gpr_pred"])
    axes[1].scatter(result["gpr_pred"], result["y_test"], alpha=0.5, label="Predictions")
    axes[1].fill_between(
        result["gpr_pred"][sorted_idx],
        (result["gpr_pred"] - 1.96 * result["gpr_std"])[sorted_idx],
        (result["gpr_pred"] + 1.96 * result["gpr_std"])[sorted_idx],
        alpha=0.2, label="95% Confidence Interval"
    )
    line_min = min(result["gpr_pred"].min(), result["y_test"].min())
    line_max = max(result["gpr_pred"].max(), result["y_test"].max())
    axes[1].plot([line_min, line_max], 
                 [line_min, line_max], 'r--', lw=2, label="Perfect Prediction")
    axes[1].set_xlabel("Predicted SOC (%)")
    axes[1].set_ylabel("Actual SOC (%)")
    axes[1].set_title(f"GPR - Tower {result['tower_id']} (RMSE: {result['gpr_rmse']:.4f}, Calibration: {result['gpr_calibration']:.1f}%)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "predictions_comparison.png"), dpi=150, bbox_inches='tight')
    print(f"   Saved: predictions_comparison.png")

    # Also save a time-series plot for SOC prediction vs actual SOC (limit to 2000 time steps)
    max_steps = min(2000, len(result["actual_soc"]))
    time_steps = np.arange(max_steps)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(time_steps, result["actual_soc"][:max_steps], label="Actual SOC", color='blue', linewidth=2)
    ax.plot(time_steps, result["gpr_soc_pred"][:max_steps], label="GPR Predicted SOC", color='orange', linewidth=2)
    ax.fill_between(
        time_steps,
        result["gpr_soc_lower"][:max_steps],
        result["gpr_soc_upper"][:max_steps],
        alpha=0.2,
        color='orange',
        label="95% SOC Confidence Interval"
    )
    ax.set_xlabel("Time Step")
    ax.set_ylabel("SOC (%)")
    ax.set_title(f"GPR SOC Time Series - Tower {result['tower_id']}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"tower_{result['tower_id']}_soc_timeseries.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"   Saved: tower_{result['tower_id']}_soc_timeseries.png")

# 2. Model Performance Comparison
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

metrics_data = {
    "RMSE": [model_performances["LinearRegression"]["rmse"], 
             model_performances["GaussianProcess"]["rmse"]],
    "MAE": [model_performances["LinearRegression"]["mae"], 
            model_performances["GaussianProcess"]["mae"]],
    "R² Score": [model_performances["LinearRegression"]["r2"], 
                 model_performances["GaussianProcess"]["r2"]]
}

for idx, (metric_name, values) in enumerate(metrics_data.items()):
    axes[idx].bar(["LinearRegression", "GPR"], 
                  [np.mean(values[0]), np.mean(values[1])],
                  yerr=[np.std(values[0]), np.std(values[1])],
                  capsize=5, alpha=0.7, color=['steelblue', 'coral'])
    axes[idx].set_ylabel(metric_name)
    axes[idx].set_title(f"Average {metric_name}")
    axes[idx].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "model_comparison.png"), dpi=150, bbox_inches='tight')
print(f"   Saved: model_comparison.png")

# 3. Uncertainty Quantification
if test_results_all:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Residuals vs Uncertainty
    result = test_results_all[0]
    residuals = np.abs(result["y_test"] - result["gpr_pred"])
    
    axes[0].scatter(result["gpr_std"], residuals, alpha=0.6)
    axes[0].set_xlabel("Predicted Uncertainty (σ)")
    axes[0].set_ylabel("Absolute Residual")
    axes[0].set_title("GPR Uncertainty vs Prediction Error")
    axes[0].grid(True, alpha=0.3)
    
    # Uncertainty distribution
    all_uncertainties = []
    for result in test_results_all:
        all_uncertainties.extend(result["gpr_std"])
    
    axes[1].hist(all_uncertainties, bins=30, alpha=0.7, edgecolor='black')
    axes[1].set_xlabel("Predicted Uncertainty (σ)")
    axes[1].set_ylabel("Frequency")
    axes[1].set_title("Distribution of GPR Uncertainties")
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "uncertainty_analysis.png"), dpi=150, bbox_inches='tight')
    print(f"   Saved: uncertainty_analysis.png")

# -------- SAVE RESULTS TO CSV --------
results_df = pd.DataFrame(test_results_all)
results_csv = os.path.join(OUTPUT_DIR, "test_results.csv")
results_df.to_csv(results_csv, index=False)
print(f"   Saved: test_results.csv")

print("\n" + "="*60)
print("GPR Analysis Complete!")
print(f"All outputs saved to: {OUTPUT_DIR}")
print("="*60)

# -------- KEY INSIGHTS --------
print("\n📌 KEY INSIGHTS:")
print(f"  • GPR provides {len(test_towers)} uncertainty estimates per prediction")
print(f"  • 95% CI calibration averaged: {np.mean([r['gpr_calibration'] for r in test_results_all]):.1f}%")
print(f"  • GPR better for: Non-linear patterns, small datasets, decision-making under uncertainty")
print(f"  • Use LinearRegression if: Speed is critical, interpretability is needed")
print(f"  • Use GPR if: Uncertainty quantification is needed, small training set, complex patterns")
