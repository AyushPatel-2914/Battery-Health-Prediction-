#!/usr/bin/env python
"""
Main Entry Point for Monthly Battery Simulation

This is a simplified entry point that delegates to scripts.
For full simulation orchestration, see:
  - scripts/run_simulation.py   : Core simulation
  - scripts/train_ml_model.py   : ML model training and testing
  - scripts/animate_simulation.py : Visualization

Usage:
  python main.py               # Run full pipeline (simulation + ML + animation)
  python main.py --sim-only    # Run just simulation
  python main.py --ml-only     # Train/test ML model
  python main.py --animate     # Visualize results
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.run_simulation import run_simulation, save_results
from ml.soc_predictor import train_soc_predictor, test_soc_predictor
from utils.visualization import animate_monthly_simulation
from models import TowerLayout
from config import SIM_CONFIG
import pandas as pd


def main():
    """Execute full simulation pipeline."""
    # Parse arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else ["--all"]
    run_sim = "--sim-only" in args or "--all" in args or not args
    run_ml = "--ml-only" in args or "--all" in args or not args
    run_anim = "--animate" in args or "--all" in args or not args

    print("=" * 70)
    print("MONTHLY BATTERY SIMULATION - REFACTORED")
    print("=" * 70)

    output_dir = None

    # 1. Run simulation
    if run_sim:
        print("\n" + "=" * 70)
        print("STAGE 1: SIMULATION")
        print("=" * 70)
        try:
            df, layout = run_simulation(noisy=True)
            output_dir = save_results(df)
        except Exception as e:
            print(f"❌ Simulation failed: {e}")
            import traceback

            traceback.print_exc()
            return

    # 2. Train/test ML model
    if run_ml:
        print("\n" + "=" * 70)
        print("STAGE 2: MACHINE LEARNING")
        print("=" * 70)
        if output_dir is None:
            # Use the same output directory as save_results (scripts/data/outputs)
            scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
            output_dir = os.path.join(scripts_dir, "data", "outputs")

        if not os.path.exists(os.path.join(output_dir, "tower_0_month_data.csv")):
            print("⚠️ No simulation data found. Run simulation first.")
        else:
            try:
                model, train_towers, std_error = train_soc_predictor(output_dir)

                # Find test towers
                available_towers = []
                for file in os.listdir(output_dir):
                    if file.startswith("tower_") and file.endswith("_month_data.csv"):
                        tower_id = int(file.split("_")[1])
                        available_towers.append(tower_id)

                available_towers = sorted(available_towers)
                test_towers = [t for t in available_towers if t not in train_towers][:5]

                if test_towers:
                    print(f"\n🧪 Testing on towers: {test_towers}")
                    results = test_soc_predictor(model, output_dir, test_towers, std_error, output_dir)
                    print(f"\n📊 Test Results:")
                    for res in results:
                        print(f"   Tower {res['tower_id']}: MAE={res['mae']:.4f}, RMSE={res['rmse']:.4f}")

            except Exception as e:
                print(f"❌ ML training failed: {e}")
                import traceback

                traceback.print_exc()

    # 3. Animate results
    if run_anim:
        print("\n" + "=" * 70)
        print("STAGE 3: VISUALIZATION")
        print("=" * 70)
        if output_dir is None:
            # Use the same output directory as save_results (scripts/data/outputs)
            scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
            output_dir = os.path.join(scripts_dir, "data", "outputs")

        combined_file = os.path.join(output_dir, "multi_tower_output.csv")
        if not os.path.exists(combined_file):
            print("⚠️ No simulation output found. Run simulation first.")
        else:
            try:
                print("📊 Loading simulation data...")
                df = pd.read_csv(combined_file)
                df["datetime"] = pd.to_datetime(df["datetime"])

                print("🏢 Creating tower layout...")
                layout = TowerLayout(SIM_CONFIG["num_towers"], SIM_CONFIG["grid_size"])

                print("🎬 Starting animation...")
                animate_monthly_simulation(df, layout, SIM_CONFIG)
            except Exception as e:
                print(f"⚠️ Animation failed: {e}")

    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
