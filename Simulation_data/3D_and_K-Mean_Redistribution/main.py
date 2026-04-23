"""Entry point for the Test simulation.

This module orchestrates the Test scenario by creating models,
running the simulation, saving the output CSV files, and
launching visualization.
"""

import os
import shutil

import numpy as np

from battery.battery_model import BatteryModel
from config.config_utils import build_noisy_config
from config.simulation_config import SIM_CONFIG
from environment.temperature_model import TemperatureModel
from network.coverage_model import CoverageModel
from network.load_sharing_model import LoadSharingModel
from network.user_model import UserModel
from simulation.multi_tower_simulator import MultiTowerSimulator
from terrain.terrain_model import TerrainModel
from terrain.tower_layout import TowerLayout
from utils.visualization import animate_monthly_simulation


def save_simulation_csv(df, output_dir):
    """Write simulation output to per-tower monthly CSV files."""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    for tid in df["tower_id"].unique():
        tower_df = df[df["tower_id"] == tid]
        filename = os.path.join(output_dir, f"tower_{tid}_month_data.csv")
        tower_df.to_csv(filename, index=False)
        print(f"[CSV] Saved: {filename}")


def build_simulation_objects(config, noisy_config):
    """Create the models and objects needed for Test simulation."""
    env = TemperatureModel(config["season"])
    user_model = UserModel(config["max_users"], noise_scale=15.0)
    coverage_model = CoverageModel(noisy_config["base_coverage_radius"])
    terrain = TerrainModel(base_factor=1.0, noise_scale=0.18)
    layout = TowerLayout(config["num_towers"], config["grid_size"])
    load_model = LoadSharingModel()
    batteries = [
        BatteryModel(
            noisy_config["battery_capacity_Wh"],
            noisy_config["idle_power"],
            config["initial_soc"],
        )
        for _ in range(config["num_towers"])
    ]
    return env, user_model, coverage_model, terrain, layout, load_model, batteries


def run_test_simulation():
    """Execute the Test simulation and show results."""
    print("🔧 Adding Gaussian noise to simulation parameters...")

    noisy_config = build_noisy_config(
        SIM_CONFIG,
        battery_noise=0.08,
        coverage_noise=0.06,
        power_noise=0.08,
    )
    print(f"   Battery parameters noise: 8.0%")
    print(f"   Coverage radius noise: 6.0%")
    print(f"   TX power noise: 8.0%")
    print(f"   User demand noise scale: 15")
    print(f"   Terrain noise scale: 0.18")

    env, user_model, coverage_model, terrain, layout, load_model, batteries = (
        build_simulation_objects(SIM_CONFIG, noisy_config)
    )

    sim = MultiTowerSimulator(
        SIM_CONFIG,
        env,
        user_model,
        coverage_model,
        terrain,
        batteries,
        layout,
        load_model,
    )

    df = sim.run()

    output_dir = os.path.join(os.path.dirname(__file__), "simulation_data")
    save_simulation_csv(df, output_dir)
    print("[OK] 5-Tower MONTH Simulation Completed")

    try:
        animate_monthly_simulation(df, layout)
    except Exception as exc:
        print(f"Animation failed: {exc}")
        print("The CSV files were generated successfully.")


if __name__ == "__main__":
    run_test_simulation()
