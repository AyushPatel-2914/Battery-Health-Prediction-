# power_and_battery_prediction_linear.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

# -------------------------------
# 1. GENERATE YOUR OWN DATASET
# -------------------------------

np.random.seed(42)
n = 3000

data = pd.DataFrame()

data['users'] = np.random.randint(5, 250, n)
data['traffic'] = data['users'] * np.random.uniform(0.8, 3.0, n)
data['temperature'] = np.random.normal(32, 6, n)
data['terrain_factor'] = np.random.uniform(0.6, 1.8, n)
data['distance_load'] = np.random.uniform(0.5, 2.0, n)

data['tx_power'] = (
    40
    + 0.4 * data['users']
    + 25 * data['terrain_factor']
    + 10 * data['distance_load']
    + np.random.normal(0, 5, n)
)

# Power consumption (W)
data['power'] = (
    0.6 * data['tx_power']
    + 0.02 * data['traffic']
    + 0.5 * data['temperature']
    + np.random.normal(0, 3, n)
)

# Battery (% remaining)
# Depends on power + load + temp (IMPORTANT LINK)
data['battery'] = (
    100
    - 0.05 * data['power']
    - 0.01 * data['traffic']
    - 0.1 * data['temperature']
    + np.random.normal(0, 2, n)
)

data['battery'] = np.clip(data['battery'], 0, 100)

# -------------------------------
# 2. PREPARE DATA
# -------------------------------

X = data[['users','traffic','temperature','terrain_factor','distance_load','tx_power']]

y_power = data['power']
y_battery = data['battery']

X_train, X_test, y_power_train, y_power_test = train_test_split(
    X, y_power, test_size=0.2, random_state=42
)

_, _, y_battery_train, y_battery_test = train_test_split(
    X, y_battery, test_size=0.2, random_state=42
)

# -------------------------------
# 3. TRAIN MODELS
# -------------------------------

power_model = LinearRegression()
battery_model = LinearRegression()

power_model.fit(X_train, y_power_train)
battery_model.fit(X_train, y_battery_train)

# Predictions
power_pred = power_model.predict(X_test)
battery_pred = battery_model.predict(X_test)

# -------------------------------
# 4. CONFIDENCE INTERVAL FUNCTION
# -------------------------------

def compute_ci(X_train, X_test, y_test, y_pred):
    residuals = y_test - y_pred
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

# Compute CI for both
power_lower, power_upper = compute_ci(X_train, X_test, y_power_test, power_pred)
battery_lower, battery_upper = compute_ci(X_train, X_test, y_battery_test, battery_pred)

# # -------------------------------
# 5. VISUALIZATION + SAVE IMAGES
# -------------------------------

# ---- Power Plot ----
plt.figure(figsize=(10,5))
plt.plot(power_pred[:100], label="Predicted Power")
plt.plot(y_power_test.values[:100], linestyle='dashed', label="Actual Power")

plt.fill_between(
    range(100),
    power_lower[:100],
    power_upper[:100],
    alpha=0.3,
    label="Confidence Interval"
)

plt.title("Power Prediction with Confidence Bounds")
plt.legend()

# SAVE IMAGE
plt.savefig("power_prediction.png", dpi=300, bbox_inches='tight')
plt.close()


# ---- Battery Plot ----
plt.figure(figsize=(10,5))
plt.plot(battery_pred[:100], label="Predicted Battery %")
plt.plot(y_battery_test.values[:100], linestyle='dashed', label="Actual Battery %")

plt.fill_between(
    range(100),
    battery_lower[:100],
    battery_upper[:100],
    alpha=0.3,
    label="Confidence Interval"
)

plt.title("Battery Prediction with Confidence Bounds")
plt.legend()

# SAVE IMAGE
plt.savefig("battery_prediction.png", dpi=300, bbox_inches='tight')
plt.close()

# -------------------------------
# 6. SAMPLE OUTPUT
# -------------------------------

print("\nSample Predictions:\n")

for i in range(5):
    print(f"Power: {power_pred[i]:.2f}W "
          f"[{power_lower[i]:.2f}, {power_upper[i]:.2f}] | "
          f"Battery: {battery_pred[i]:.2f}% "
          f"[{battery_lower[i]:.2f}, {battery_upper[i]:.2f}]")