# power_prediction_linear.py

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

# Target: Power consumption
data['power'] = (
    0.6 * data['tx_power']
    + 0.02 * data['traffic']
    + 0.5 * data['temperature']
    + np.random.normal(0, 3, n)
)

# -------------------------------
# 2. PREPARE DATA
# -------------------------------

X = data[['users','traffic','temperature','terrain_factor','distance_load','tx_power']]
y = data['power']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -------------------------------
# 3. LINEAR REGRESSION MODEL
# -------------------------------

model = LinearRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

# -------------------------------
# 4. CONFIDENCE INTERVAL (ANALYTICAL)
# -------------------------------

# Residuals
residuals = y_test - y_pred

# Estimate variance
sigma_sq = np.var(residuals)

# Add intercept column manually
X_test_mat = np.hstack([np.ones((X_test.shape[0],1)), X_test.values])
X_train_mat = np.hstack([np.ones((X_train.shape[0],1)), X_train.values])

# Compute (X^T X)^-1
XtX_inv = np.linalg.inv(X_train_mat.T @ X_train_mat)

# Variance of predictions
pred_var = np.array([
    sigma_sq * (1 + x.T @ XtX_inv @ x)
    for x in X_test_mat
])

pred_std = np.sqrt(pred_var)

# 95% confidence interval
lower = y_pred - 1.96 * pred_std
upper = y_pred + 1.96 * pred_std

# -------------------------------
# 5. VISUALIZATION
# -------------------------------

plt.figure(figsize=(10,5))

plt.plot(y_pred[:100], label="Predicted Power")
plt.plot(y_test.values[:100], label="Actual Power", linestyle='dashed')

plt.fill_between(
    range(100),
    lower[:100],
    upper[:100],
    alpha=0.3,
    label="Confidence Interval (95%)"
)

plt.legend()
plt.title("Linear Regression: Power Prediction with Confidence Bounds")
plt.xlabel("Sample Index")
plt.ylabel("Power")
plt.show()

# -------------------------------
# 6. PRINT SAMPLE OUTPUT
# -------------------------------

print("\nSample Predictions with Confidence:\n")
for i in range(5):
    print(f"Pred: {y_pred[i]:.2f} | CI: [{lower[i]:.2f}, {upper[i]:.2f}] | Actual: {y_test.values[i]:.2f}")