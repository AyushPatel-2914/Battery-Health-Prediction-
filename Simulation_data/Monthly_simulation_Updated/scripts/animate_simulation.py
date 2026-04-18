"""
Animation Visualization Script

Visualizes simulation results with animated towers and users.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config import SIM_CONFIG
from models import TowerLayout
from utils.visualization import animate_monthly_simulation


def main():
    """Animate saved simulation results."""
    data_dir = os.path.join(os.path.dirname(__file__), "data", "outputs")
    combined_file = os.path.join(data_dir, "multi_tower_output.csv")

    if not os.path.exists(combined_file):
        print(f"❌ Data file not found: {combined_file}")
        print("   Run run_simulation.py first to generate simulation data.")
        return

    print("📊 Loading simulation data...")
    df = pd.read_csv(combined_file)
    df["datetime"] = pd.to_datetime(df["datetime"])

    print("🏢 Creating tower layout...")
    layout = TowerLayout(SIM_CONFIG["num_towers"], SIM_CONFIG["grid_size"])

    print("🎬 Starting animation...")
    try:
        animate_monthly_simulation(df, layout, SIM_CONFIG)
    except Exception as e:
        print(f"❌ Animation failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
