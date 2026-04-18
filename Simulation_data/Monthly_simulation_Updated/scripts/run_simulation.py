"""
Main Simulation Script

Runs the full multi-tower battery simulation with configurable noise.
"""

import numpy as np
import os
import shutil

from config import SIM_CONFIG
from models import (
    TemperatureModel,
    UserModel,
    CoverageModel,
    TerrainModel,
    TowerLayout,
    LoadSharingModel,
    BatteryModel,
)
from simulation import MultiTowerSimulator


def run_simulation(noisy=True):
    """
    Run full multi-tower simulation.

    Args:
        noisy: If True, add Gaussian noise to simulation parameters

    Returns:
        Simulation results DataFrame and models layout
    """
    # Create noisy config if requested
    if noisy:
        print("🔧 Adding Gaussian noise to simulation parameters...")
        noisy_config = SIM_CONFIG.copy()

        battery_noise = 0.05
        noisy_config["battery_capacity_Wh"] = SIM_CONFIG["battery_capacity_Wh"] * (
            1 + np.random.normal(0, battery_noise)
        )
        noisy_config["idle_power"] = SIM_CONFIG["idle_power"] * (
            1 + np.random.normal(0, battery_noise)
        )

        coverage_noise = 0.03
        noisy_config["base_coverage_radius"] = SIM_CONFIG["base_coverage_radius"] * (
            1 + np.random.normal(0, coverage_noise)
        )

        power_noise = 0.05
        noisy_config["base_tx_power"] = SIM_CONFIG["base_tx_power"] * (
            1 + np.random.normal(0, power_noise)
        )

        print(f"   Battery noise: {battery_noise*100}%")
        print(f"   Coverage noise: {coverage_noise*100}%")
        print(f"   TX power noise: {power_noise*100}%")
    else:
        noisy_config = SIM_CONFIG.copy()

    # Create model objects
    print("\n📦 Initializing models...")
    env = TemperatureModel(SIM_CONFIG["season"])
    user_model = UserModel(SIM_CONFIG["max_users"], noise_scale=7.0)
    coverage_model = CoverageModel(noisy_config["base_coverage_radius"])
    terrain = TerrainModel(base_factor=1.0, noise_scale=0.1)
    layout = TowerLayout(SIM_CONFIG["num_towers"], SIM_CONFIG["grid_size"])
    load_model = LoadSharingModel()

    batteries = [
        BatteryModel(
            noisy_config["battery_capacity_Wh"],
            noisy_config["idle_power"],
            SIM_CONFIG["initial_soc"],
        )
        for _ in range(SIM_CONFIG["num_towers"])
    ]

    # Run simulation
    print(f"\n🚀 Running {SIM_CONFIG['sim_days']}-day, {SIM_CONFIG['num_towers']}-tower simulation...")
    sim = MultiTowerSimulator(
        SIM_CONFIG, env, user_model, coverage_model, terrain, batteries, layout, load_model
    )

    df = sim.run()
    print(f"✅ Simulation complete. Generated {len(df)} time steps.")

    return df, layout


def save_results(df, output_dir=None):
    """
    Save simulation results to CSV files.

    Args:
        df: Simulation DataFrame
        output_dir: Output directory (default: data/outputs)
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "data", "outputs")

    os.makedirs(output_dir, exist_ok=True)

    # Clean old data
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.endswith(".csv"):
                os.remove(os.path.join(output_dir, file))

    # Save per-tower data
    print(f"\n💾 Saving simulation data to {output_dir}...")
    for tid in sorted(df["tower_id"].unique()):
        tower_df = df[df["tower_id"] == tid]
        filename = os.path.join(output_dir, f"tower_{tid}_month_data.csv")
        tower_df.to_csv(filename, index=False)
        print(f"   ✓ {filename}")

    # Save combined multi-tower data
    combined_file = os.path.join(output_dir, "multi_tower_output.csv")
    df.to_csv(combined_file, index=False)
    print(f"   ✓ {combined_file}")

    print("[OK] All simulation data saved")
    return output_dir


if __name__ == "__main__":
    # Run simulation
    df, layout = run_simulation(noisy=True)

    # Save results to data/outputs
    output_dir = save_results(df)

    # Try animation (optional)
    try:
        from utils.visualization import animate_monthly_simulation

        print("\n🎬 Starting animation...")
        animate_monthly_simulation(df, layout, SIM_CONFIG)
    except Exception as e:
        print(f"⚠️ Animation skipped: {e}")
        print("   (CSV files were generated successfully)")
