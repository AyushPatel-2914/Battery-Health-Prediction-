"""Simulation configuration settings for the Test scenario.

The configuration dictionary centralizes timing, battery, network,
and terrain parameters required by the simulation.
"""

SIM_CONFIG = {
    "start_datetime": "2026-05-15 00:00:00",
    "season": "summer",
    "time_step_minutes": 5,
    "battery_capacity_Wh": 5000,
    "initial_soc": 100,
    "base_tx_power": 120,
    "idle_power": 60,
    "max_users": 500,
    "display_users": 50,
    "base_coverage_radius": 250,
    "num_towers": 15,
    "grid_size": 1000,
    "sim_days": 30,
}
