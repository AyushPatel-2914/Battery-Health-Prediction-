# from_csv_fixed.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

# -------------------------------
# 1. LOAD CSV (FIX PATH HERE)
# -------------------------------

data = pd.read_csv("tower_0_month_data.csv")

# -------------------------------
# 2. FEATURE ENGINEERING
# -------------------------------

# Add time feature
data['hour'] = pd.to_datetime(data['datetime']).dt.hour

# Features (MATCH YOUR CSV)
X = data[[
    'effective_users',
    'coverage_load',
    'temperature_degC',
    'tx_power_W',
    'hour'
]]

# Targets
y_power = data['power_consumption_W']
y_battery = data['battery_soc_percent']

# -------------------------------
# 3. TRAIN TEST SPLIT
# -------------------------------

X_train, X_test, y_power_train, y_power_test = train_test_split(
    X, y_power, test_size=0.2, random_state=42
)

_, _, y_battery_train, y_battery_test = train_test_split(
    X, y_battery, test_size=0.2, random_state=42
)

# -------------------------------
# 4. MODELS
# -------------------------------

power_model = LinearRegression()
battery_model = LinearRegression()

power_model.fit(X_train, y_power_train)
battery_model.fit(X_train, y_battery_train)

power_pred = power_model.predict(X_test)
battery_pred = battery_model.predict(X_test)

# -------------------------------
# 5. CONFIDENCE INTERVAL FUNCTION
# -------------------------------

def compute_ci(X_train, X_test, y_test, y_pred):
    residuals = y_test.values - y_pred
    sigma_sq = np.var(residuals)

    X_train_mat = np.hstack([np.ones((X_train.shape[0],1)), X_train.values])
    X_test_mat = np.hstack([np.ones((X_test.shape[0],1)), X_test.values])

    XtX_inv = np.linalg.inv(X_train_mat.T @ X_train_mat)

    pred_var = np.array([
        sigma_sq * (1 + x.T @ XtX_inv @ x)
        for x in X_test_mat
    ])

    pred_std = np.sqrt(pred_var)

    lower = y_pred - 1.96 * pred_std
    upper = y_pred + 1.96 * pred_std

    return lower, upper

# Compute CI
power_lower, power_upper = compute_ci(X_train, X_test, y_power_test, power_pred)
battery_lower, battery_upper = compute_ci(X_train, X_test, y_battery_test, battery_pred)

# -------------------------------
# 6. FIX FOR YOUR ERROR 🔥
# -------------------------------

# Use correct length instead of range(100)
n_plot = min(100, len(power_pred))
x_axis = range(n_plot)

# -------------------------------
# 7. SAVE POWER PLOT
# -------------------------------

plt.figure(figsize=(10,5))

plt.plot(x_axis, power_pred[:n_plot], label="Predicted Power")
plt.plot(x_axis, y_power_test.values[:n_plot], linestyle='dashed', label="Actual Power")

plt.fill_between(
    x_axis,
    power_lower[:n_plot],
    power_upper[:n_plot],
    alpha=0.3,
    label="Confidence Interval"
)

plt.legend()
plt.title("Power Prediction")
plt.savefig("power_from_csv.png", dpi=300, bbox_inches='tight')
plt.close()

# -------------------------------
# 8. SAVE BATTERY PLOT
# -------------------------------

plt.figure(figsize=(10,5))

plt.plot(x_axis, battery_pred[:n_plot], label="Predicted Battery")
plt.plot(x_axis, y_battery_test.values[:n_plot], linestyle='dashed', label="Actual Battery")

plt.fill_between(
    x_axis,
    battery_lower[:n_plot],
    battery_upper[:n_plot],
    alpha=0.3,
    label="Confidence Interval"
)

plt.legend()
plt.title("Battery Prediction")
plt.savefig("battery_from_csv.png", dpi=300, bbox_inches='tight')
plt.close()

# -------------------------------
# 9. SAMPLE OUTPUT
# -------------------------------

print("\nSample Predictions:\n")

for i in range(min(5, len(power_pred))):
    print(f"Power: {power_pred[i]:.2f}W "
          f"[{power_lower[i]:.2f}, {power_upper[i]:.2f}] | "
          f"Battery: {battery_pred[i]:.2f}% "
          f"[{battery_lower[i]:.2f}, {battery_upper[i]:.2f}]")