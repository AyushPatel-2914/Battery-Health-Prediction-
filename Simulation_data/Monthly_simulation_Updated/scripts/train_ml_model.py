"""
ML Training and Testing Script

Trains SOC prediction model and evaluates on separate tower set.
"""

import os
from ml.soc_predictor import train_soc_predictor, test_soc_predictor


def main():
    """Train and test SOC prediction model."""
    # Data directory
    data_dir = os.path.join(os.path.dirname(__file__), "data", "outputs")

    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        print("   Run run_simulation.py first to generate simulation data.")
        return

    # Train model on 5 towers
    print("🤖 Starting ML model training and testing...\n")
    model, train_towers, std_error = train_soc_predictor(data_dir)

    # Find all towers for testing
    available_towers = []
    for file in os.listdir(data_dir):
        if file.startswith("tower_") and file.endswith("_month_data.csv"):
            tower_id = int(file.split("_")[1])
            available_towers.append(tower_id)

    available_towers = sorted(available_towers)
    test_towers = [t for t in available_towers if t not in train_towers][:5]

    if not test_towers:
        print("❌ Not enough unused towers for testing.")
        test_towers = train_towers  # Fall back to training towers

    print(f"🧪 Testing on towers: {test_towers}\n")

    # Test model
    results = test_soc_predictor(model, data_dir, test_towers, std_error, output_dir=data_dir)

    # Summary
    print(f"\n🎉 ML Pipeline Complete!")
    print(f"📊 Test Results Summary:")
    for res in results:
        print(f"   Tower {res['tower_id']}: MAE={res['mae']:.4f}, RMSE={res['rmse']:.4f}")


if __name__ == "__main__":
    main()
