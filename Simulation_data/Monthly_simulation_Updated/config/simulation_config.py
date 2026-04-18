"""
Configuration Module

Central configuration for multi-tower battery simulation.
"""

SIM_CONFIG = {
    # Simulation timing
    "start_datetime": "2026-05-15 00:00:00",
    "season": "summer",
    "time_step_minutes": 5,
    "sim_days": 30,
    
    # Battery parameters
    "battery_capacity_Wh": 5000,
    "initial_soc": 100,
    
    # Power parameters
    "base_tx_power": 120,
    "idle_power": 60,
    
    # User and coverage parameters
    "max_users": 500,
    "display_users": 50,
    "base_coverage_radius": 250,
    
    # Tower and grid parameters
    "num_towers": 15,
    "grid_size": 1000,
}