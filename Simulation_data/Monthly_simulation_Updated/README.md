# Monthly Battery Simulation - Refactored Architecture

## Overview

This is a **modular, physics-based multi-tower battery simulation** for generating synthetic telecom tower data. It combines deterministic environmental models with stochastic user behavior to simulate 30 days of battery, network, and temperature data.

## Directory Structure (Refactored)

```
Monthly_simulation_Updated/
│
├── config/                    # Configuration
│   ├── __init__.py
│   └── simulation_config.py   # Central config (SIM_CONFIG dictionary)
│
├── models/                    # Physics Models (consolidated)
│   ├── __init__.py
│   ├── battery.py             # BatteryModel: SOC, power, charging
│   ├── environment.py         # TemperatureModel: daily/seasonal cycles
│   ├── network.py             # UserModel, CoverageModel, LoadSharingModel, TrafficModel
│   ├── terrain.py             # TerrainModel, TowerLayout
│   └── positioning.py         # TowerPositioning, UserPositioning
│
├── simulation/                # Simulation Engine
│   ├── __init__.py
│   └── multi_tower_simulator.py  # MultiTowerSimulator: core time-loop
│
├── ml/                        # Machine Learning
│   ├── __init__.py
│   └── soc_predictor.py       # train_soc_predictor(), test_soc_predictor()
│
├── utils/                     # Utilities
│   ├── __init__.py
│   ├── data_logger.py         # plot_results()
│   └── visualization.py       # animate_monthly_simulation()
│
├── scripts/                   # Standalone Scripts
│   ├── __init__.py
│   ├── run_simulation.py      # Execute simulation + save results
│   ├── train_ml_model.py      # Train/test ML model
│   └── animate_simulation.py  # Visualize results
│
├── data/
│   └── outputs/               # Output CSVs and plots
│
├── main.py                    # **Simple entry point** (delegates to scripts)
├── EXPLANATION.md             # Detailed explanation of models
├── Setup.md                   # Setup instructions
└── README.md                  # This file
```

## Key Improvements

### ✅ **Modularization**
- **Models consolidated**: All physics models are now in `models/` package with proper imports
- **Separated concerns**:
  - `models/` = domain logic (battery, environment, network, terrain)
  - `simulation/` = engine that orchestrates models
  - `ml/` = machine learning utilities
  - `utils/` = visualization and plotting
  - `scripts/` = standalone executable scripts
  - `config/` = central configuration

### ✅ **Code Quality**
- **Full docstrings** on all classes and functions
- **Proper `__init__.py`** files for all packages
- **Clear imports**: `from models import BatteryModel, TemperatureModel, ...`
- **No circular dependencies**

### ✅ **File Organization**
- **Output files in `data/outputs/`**: All generated CSVs and PNGs now go to one place
- **Scripts separate from models**: No ML code mixed with simulation
- **Clean root**: Only `main.py`, config, and documentation in root

### ✅ **Entry Points**
- **`main.py`**: Universal entry point that manages full pipeline
- **`scripts/run_simulation.py`**: Just run simulation
- **`scripts/train_ml_model.py`**: Just train ML model
- **`scripts/animate_simulation.py`**: Just visualize

## Usage

### Option 1: Full Pipeline (Simulation → ML → Animation)

```bash
python main.py
```

### Option 2: Selective Execution

```bash
# Simulation only
python main.py --sim-only

# ML training and testing only (requires pre-existing simulation data)
python main.py --ml-only

# Animation only (requires pre-existing simulation data)
python main.py --animate

# Specific scripts
python scripts/run_simulation.py
python scripts/train_ml_model.py
python scripts/animate_simulation.py
```

## Model Overview

### **config/simulation_config.py**
Central configuration dictionary with all parameters:
- Timing: start date, season, simulation days, time step
- Battery: capacity, idle power, initial SOC
- Power: TX power, idle power
- Users: max users, display users, coverage radius
- Grid: number of towers, grid size

### **models/battery.py** - `BatteryModel`
- Computes power consumption:
  - Idle base power
  - User-driven load (0.35 W/user)
  - TX power loss (0.0009 × tx_power²)
  - Coverage load term (2 × coverage_load)
  - Temperature stress (0.03 × exp(temp/40))
- Updates SOC: `soc -= (energy / capacity) * 100`
- Auto-recharge when SOC=0

### **models/environment.py** - `TemperatureModel`
- Daily sinusoidal cycle: peak at noon, low at night
- Seasonal variation: mean/amplitude adjust for summer/winter
- Gaussian noise: ±0.5°C random fluctuation

### **models/network.py** - Network Models
- **UserModel**: Sin² daily pattern, peaks at 8 AM
- **CoverageModel**: Circular coverage with terrain scaling
- **LoadSharingModel**: Redistribution by SOC capacity
- **TrafficModel**: Base load + Poisson bursts

### **models/terrain.py** - Spatial Models
- **TerrainModel**: Random scaling factor (0.8–1.3)
- **TowerLayout**: Places towers on MAP track (if available) or random grid

### **models/positioning.py** - Position Assignment
- **TowerPositioning**: Handles tower placement on MAP track or random grid
- **UserPositioning**: Assigns users to nearest towers within coverage radius

### **simulation/multi_tower_simulator.py** - Engine
- Time-loop over 30 days × 288 steps/day = 8,640 time steps
- Per tower, per timestep:
  1. Sample temperature
  2. Sample total users
  3. Assign users to nearest towers
  4. Compute coverage load
  5. Calculate power consumption
  6. Update battery SOC
- Output: DataFrame with columns: datetime, tower_id, x, y, temperature, users, coverage_radius, coverage_load, tx_power, power, soc

### **ml/soc_predictor.py** - SOC Prediction
- Train on 5 towers → `LinearRegression` model
- Test on 5 different towers → predictions + 95% CI
- Features: prev_soc, hour, temperature, users, coverage_load, tx_power
- Output: MAE, RMSE, plots with confidence bands

## Data Flow

```
config/SIM_CONFIG
    ↓
Create models (Battery, Temperature, User, Coverage, Terrain, TowerLayout)
    ↓
FOR each timestep (8,640 total):
    ├─ Get temperature
    ├─ Get user demand
    ├─ Assign users to towers
    ├─ Calculate power per tower
    └─ Update battery SOC per tower
    ↓
Output: DataFrame (tower × timestep → batch)
    ↓
Save: data/outputs/tower_*.csv + multi_tower_output.csv
    ↓
Plot: Animation or static plots
    ↓
Train ML: LinearRegression on 5 towers
    ↓
Test ML: Evaluate on 5 other towers
```

## Output Files

After running `python main.py`:

```
data/outputs/
├── tower_0_month_data.csv          # Tower 0 monthly data (5-min resolution)
├── tower_1_month_data.csv          # Tower 1 monthly data
├── ...
├── tower_14_month_data.csv
├── multi_tower_output.csv          # Combined all towers
├── tower_0_prediction_monthly.png  # ML prediction plot (if ML run)
├── tower_1_prediction_monthly.png
└── ...
```

Each CSV has columns:
- `datetime`: Timestamp
- `tower_id`: Tower ID (0-14)
- `x_m`, `y_m`: Position (meters)
- `temperature_degC`: Ambient temperature
- `effective_users`: Users assigned to tower
- `coverage_radius_m`: Coverage radius
- `coverage_load`: Normalized user density
- `tx_power_W`: Transmission power
- `power_consumption_W`: Total power draw
- `battery_soc_percent`: State of charge (0-100%)

## API Examples

### Run Simulation Programmatically

```python
from scripts.run_simulation import run_simulation, save_results

# Run simulation
df, layout = run_simulation(noisy=True)

# Save results
output_dir = save_results(df, output_dir="my_outputs")

# Animate
from utils.visualization import animate_monthly_simulation
animate_monthly_simulation(df, layout)
```

### Train ML Model

```python
from ml.soc_predictor import train_soc_predictor, test_soc_predictor

model, train_towers, std_error = train_soc_predictor("data/outputs")
results = test_soc_predictor(model, "data/outputs", [5,6,7,8,9], std_error)
```

## Previous vs. Refactored

### Before (Messy)
- ❌ Model files scattered across `battery/`, `environment/`, `network/`, `terrain/`
- ❌ No `__init__.py` files
- ❌ Output CSVs/PNGs mixed in root directory
- ❌ ML code in root `ml_model.py`
- ❌ Complex `main.py` with animation, noise, simulation all mixed
- ❌ Old folders like `previously_used/` kept around
- ❌ `simulation_data/` and root both had output files

### After (Clean)
- ✅ Models consolidated: `models/battery.py`, `models/network.py`, etc.
- ✅ Proper package structure with `__init__.py`
- ✅ All outputs in `data/outputs/`
- ✅ ML code in dedicated `ml/` package
- ✅ Modular `scripts/` for independent execution
- ✅ Single entry point `main.py` that delegates
- ✅ Old unused folders removed
- ✅ Clear separation of concerns

## Testing the Refactor

```bash
# Test imports
python -c "from models import BatteryModel; print('✓ Models OK')"
python -c "from simulation import MultiTowerSimulator; print('✓ Simulation OK')"
python -c "from ml.soc_predictor import train_soc_predictor; print('✓ ML OK')"

# Test full pipeline
python main.py

# Test individual scripts
python scripts/run_simulation.py --help
python scripts/train_ml_model.py --help
python scripts/animate_simulation.py --help
```

## Next Steps

### To extend or modify:
1. **Add new model**: Create new file in `models/`, update `models/__init__.py`
2. **Change simulation**: Edit `simulation/multi_tower_simulator.py` or config
3. **Improve ML**: Edit `ml/soc_predictor.py`, add new models
4. **Add visualization**: New functions in `utils/visualization.py`

### To integrate into pipeline:
1. Create script in `scripts/` that imports from `models/`, `simulation/`, `ml/`, `utils/`
2. Call from `main.py` with command-line flag
3. Follow docstring pattern for consistency

## Dependencies

- numpy, pandas: Data handling
- matplotlib: Visualization
- scikit-learn: ML
- python 3.8+

## Performance Notes

- **30-day sim** with 15 towers @ 5-min resolution = ~130k rows
- **ML training** on 5 towers: <1 second
- **Animation**: ~30 seconds (180 frames @ 200ms/frame)
- **Total pipeline**: ~5-10 minutes

---

**Refactored:** April 2026  
**Purpose:** Physics-based multi-tower battery simulation for ML training  
**Status:** Production-ready
