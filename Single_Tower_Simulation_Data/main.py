from config.simulation_config import SIM_CONFIG

from environment.temperature_model import TemperatureModel
from network.user_model import UserModel
from network.coverage_model import CoverageModel
from terrain.terrain_model import TerrainModel
from battery.battery_model import BatteryModel
from simulation.single_day_simulator import SingleDaySimulator
from output.data_logger import plot_results


env = TemperatureModel(SIM_CONFIG["season"])

user_model = UserModel(
    SIM_CONFIG["max_users"]
)

coverage_model = CoverageModel(
    SIM_CONFIG["base_coverage_radius"]
)

terrain = TerrainModel()

battery = BatteryModel(
    SIM_CONFIG["battery_capacity_Wh"],
    SIM_CONFIG["idle_power"],
    SIM_CONFIG["initial_soc"]
)

sim = SingleDaySimulator(
    SIM_CONFIG,
    env,
    user_model,
    coverage_model,
    terrain,
    battery
)

df = sim.run()

df.to_csv("simulation_output.csv", index=False)

plot_results(df)