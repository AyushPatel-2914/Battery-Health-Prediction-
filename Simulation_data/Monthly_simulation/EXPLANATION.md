# Monthly Simulation: What This Folder Does

This folder generates synthetic **30-day multi-tower battery and network data** at 5-minute resolution, then uses that data to train a simple SOC prediction model.

## Main purpose

- Simulate realistic telecom tower behavior over time.
- Track power consumption and battery SOC under changing users, temperature, terrain, and coverage.
- Export tower-wise monthly CSV data for ML training/testing.

## High-level flow

1. `main.py` loads `SIM_CONFIG` and creates all model objects.
2. `simulation/multi_tower_simulator.py` runs the time loop.
3. For each time step and each tower, it computes:
   - temperature
   - effective users (after SOC-based load sharing)
   - coverage radius and coverage load
   - tx power and total power draw
   - updated battery SOC
4. It writes one monthly CSV per tower:
   - `tower_0_month_data.csv` ... `tower_4_month_data.csv`
5. `ml_model.py` reads these CSVs and trains one Linear Regression model per tower to predict SOC drop, then saves plots.

## Folder/module breakdown

- `config/simulation_config.py`
  - Central simulation settings (start date, days, time step, battery capacity, users, towers, grid size, etc.).

- `environment/temperature_model.py`
  - Temperature follows a sinusoidal day cycle + noise.
  - Season controls mean and amplitude.

- `network/user_model.py`
  - User demand follows a day activity curve (`sin^2`) + random noise.

- `terrain/terrain_model.py`
  - Generates random terrain factor per step (`~0.8 to 1.3`).

- `terrain/tower_layout.py`
  - Randomly places towers in a 2D grid and keeps fixed positions during a run.

- `network/coverage_model.py`
  - Coverage radius scales with terrain.
  - Coverage load is derived from user density over circular area.

- `network/load_sharing_model.py`
  - Redistributes total users among towers by current SOC share.
  - Towers with higher SOC get more effective load.

- `battery/battery_model.py`
  - Computes power:
    - idle base power
    - user-driven load
    - nonlinear tx power term (`tx_power^2`)
    - coverage load term
    - temperature stress term (`exp(temp/40)`)
  - Updates SOC by converting power to consumed energy and clamping to `>= 0`.

- `simulation/multi_tower_simulator.py`
  - Core engine that iterates all time steps and towers.
  - Produces DataFrame with full telemetry.

- `simulation/single_day_simulator.py`
  - Single-tower/day version of the same simulation logic.

- `output/data_logger.py`
  - Optional helper plotter (mainly for single-tower style columns).

- `ml_model.py`
  - Loads monthly tower CSVs.
  - Builds temporal features (`prev_soc`, `soc_drop`, `hour`).
  - Trains Linear Regression and reconstructs predicted SOC.
  - Saves plot per tower:
    - `tower_<id>_prediction_linear_month.png`

## Key simulation settings currently used

From `config/simulation_config.py` and `main.py`:

- `sim_days = 30`
- `time_step_minutes = 5`
- `num_towers = 5`
- `battery_capacity_Wh = 5000`
- `initial_soc = 100`
- `base_tx_power = 120`
- `idle_power = 60`
- `max_users = 180`
- `base_coverage_radius = 250`

This gives `30 * 24 * 60 / 5 = 8640` time steps per tower.

## Output schema (`tower_<id>_month_data.csv`)

Each row is one time step for one tower:

- `datetime`
- `tower_id`
- `x_m`, `y_m`
- `temperature_degC`
- `effective_users`
- `coverage_radius_m`
- `coverage_load`
- `tx_power_W`
- `power_consumption_W`
- `battery_soc_percent`

## How to run

Run from this folder:

```powershell
python main.py
python ml_model.py
```

Expected generated files:

- monthly CSV per tower
- prediction plot per tower (`tower_<id>_prediction_linear_month.png`)

## Notes

- Results vary run-to-run because random noise is used in temperature, users, terrain, and layout.
- Load sharing is currently SOC-weighted only (distance/coverage constraints are not enforced there).
- `Setup.md` contains planning notes, while this file documents the implemented code flow.
