# Simulation_data/Test

This folder contains the `Final_Digital_Twin` simulation package used by MineInsite.
It is organized to keep only the two main entrypoints at the package root,
while separating all other functionality into focused folders.

## Purpose

The `Final_Digital_Twin` package simulates battery-powered tower behavior and evaluates
how environmental, user and coverage factors influence battery SOC over time.
It also includes a standalone ML workflow for training a simple model on
simulation output.

## Top-level files

- `main.py`
  - The main orchestrator for the `Final_Digital_Twin` simulation.
  - Builds the full simulation object graph from `config` and model folders.
  - Runs the multi-tower monthly simulation.
  - Writes per-tower CSV outputs to `simulation_data/`.
  - Launches the animation visualization.

- `ml_model.py`
  - Loads generated simulation CSV files from `simulation_data/`.
  - Trains a linear regression model on a subset of towers.
  - Tests the trained model on a separate set of towers.
  - Saves prediction plots for analysis.

- `__init__.py`
  - Marks this folder as a Python package.

## Folder-by-folder breakdown

### `battery/`
Contains the tower battery model and SOC behavior.

- `battery_model.py`
  - Simulates battery power draw and state-of-charge changes.
  - Uses idle draw, active user demand, transmit power, coverage load,
    and temperature to compute energy consumption.
  - Includes a simple recharge/reset mechanism when SOC reaches zero.

### `config/`
Holds simulation configuration data and helpers for noisy parameter generation.

- `simulation_config.py`
  - Defines `SIM_CONFIG`, the central configuration dictionary.
  - Includes parameters such as start date, time step, tower count, power,
    coverage radius, battery capacity, grid size, and simulation duration.

- `config_utils.py`
  - Builds a noisy copy of the base configuration.
  - Adds controlled random variation to battery capacity, idle power,
    coverage radius, and TX power.
  - Keeps the original `SIM_CONFIG` unchanged while creating one noisy run.

### `environment/`
Contains environment-related models.

- `temperature_model.py`
  - Returns a temperature value for any hour of the day.
  - Supports seasonal settings like summer and winter.
  - Adds natural daily sinusoidal variation plus small random noise.

### `network/`
Contains user and wireless network models.

- `user_model.py`
  - Computes user demand as a function of hour-of-day.
  - Uses a sinusoidal daily pattern plus noise to simulate active users.

- `traffic_model.py`
  - Provides an alternate traffic estimate model.
  - Uses a base traffic shape plus random burst events.

- `coverage_model.py`
  - Computes tower coverage radius after terrain adjustment.
  - Estimates load based on user density inside a coverage area.

- `load_sharing_model.py`
  - Redistributes users between towers based on battery state.
  - Uses remaining SOC as a proxy for available tower capacity.

### `simulation/`
Contains the core simulation engines.

- `multi_tower_simulator.py`
  - Runs the full multi-tower scenario over the configured period.
  - Generates time steps, environment values, user load, tower coverage,
    power consumption, and battery SOC for every tower.
  - Returns a consolidated pandas DataFrame with the result rows.

- `single_day_simulator.py`
  - Provides a simpler 24-hour simulation path.
  - Useful for debugging or comparing a single day against the full month.

### `terrain/`
Contains terrain and placement utilities.

- `terrain_model.py`
  - Produces a terrain adjustment factor via noisy sampling.
  - Used to change coverage radius and power slightly across towers.

- `terrain_surface.py`
  - Builds a 3D surface mesh for visualization.
  - Projects 2D tower and user coordinates onto that surface.

- `tower_layout.py`
  - Chooses tower positions for the simulation.
  - Prefers existing MAP waypoint route positions if the top-level
    `MAP/waypoints.pkl` file is available.
  - Falls back to random positions if no MAP route exists.

### `utils/`
Contains supporting helpers used by both simulation and visualization.

- `data_utils.py`
  - Builds time-series summaries from raw simulation output.
  - Prepares load and battery SOC series used by the animation.

- `map_utils.py`
  - Loads the route track from the global `MAP` folder.
  - Builds user trajectory sequences along the route for animation.

- `visualization.py`
  - Creates a 3-panel animation of the monthly simulation.
  - Shows the terrain surface, user motion, tower loads, and battery SOC.

### `simulation_data/`
Contains generated simulation output files.

- This folder is created by `main.py` during a run.
- It stores files like `tower_0_month_data.csv`, `tower_1_month_data.csv`, etc.
- `ml_model.py` reads from this folder to train and evaluate the ML model.

### `previous_datasets/`
A place for legacy or example outputs from past runs.

- Can be used as a reference dataset if you do not want to regenerate data.

## How to use this package

1. Run `main.py` first.
   - This generates the per-tower CSV files in `simulation_data/`.
   - It also launches the animation if the visualization dependencies are available.

2. Run `ml_model.py` next.
   - This loads the generated CSV files.
   - It trains a linear regression model on selected towers.
   - It tests predictions on different towers and saves plots.

## Why this layout exists

- `main.py` and `ml_model.py` are intentionally kept at the root so the
  package entrypoints are obvious.
- Each folder contains one clear responsibility:
  - battery physics, configuration, environment, network, simulation, terrain,
    and utilities.
- This makes it easy for new developers to find the code they need.

## Quick navigation guide

- If you want to change how tower batteries behave: edit `battery/battery_model.py`.
- If you want to change the scenario setup: edit `config/simulation_config.py`.
- If you want to change user demand: edit `network/user_model.py` or `network/traffic_model.py`.
- If you want to change how the simulation runs: edit `simulation/multi_tower_simulator.py`.
- If you want to update the animation: edit `utils/visualization.py`.
- If you want to change tower placement: edit `terrain/tower_layout.py`.
