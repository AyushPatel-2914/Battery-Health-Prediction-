from config.simulation_config import SIM_CONFIG

from environment.temperature_model import TemperatureModel
from network.user_model import UserModel
from network.coverage_model import CoverageModel
from terrain.terrain_model import TerrainModel
from terrain.tower_layout import TowerLayout
from network.load_sharing_model import LoadSharingModel
from battery.battery_model import BatteryModel
from simulation.multi_tower_simulator import MultiTowerSimulator


# ---------- CREATE OBJECTS ----------

env = TemperatureModel(
    SIM_CONFIG["season"]
)

user_model = UserModel(
    SIM_CONFIG["max_users"]
)

coverage_model = CoverageModel(
    SIM_CONFIG["base_coverage_radius"]
)

terrain = TerrainModel()

layout = TowerLayout(
    SIM_CONFIG["num_towers"],
    SIM_CONFIG["grid_size"]
)

load_model = LoadSharingModel()

batteries = [
    BatteryModel(
        SIM_CONFIG["battery_capacity_Wh"],
        SIM_CONFIG["idle_power"],
        SIM_CONFIG["initial_soc"]
    )
    for _ in range(SIM_CONFIG["num_towers"])
]


# ---------- RUN SIMULATION ----------

sim = MultiTowerSimulator(
    SIM_CONFIG,
    env,
    user_model,
    coverage_model,
    terrain,
    batteries,
    layout,
    load_model
)

df = sim.run()

# ---------- SAVE SEPARATE CSV FOR EACH TOWER ----------

for tid in df["tower_id"].unique():

    tower_df = df[df["tower_id"] == tid]

    filename = f"tower_{tid}_day_data.csv"

    tower_df.to_csv(filename, index=False)

print("Separate tower CSV files generated ✔")

print("Simulation Completed ✔")