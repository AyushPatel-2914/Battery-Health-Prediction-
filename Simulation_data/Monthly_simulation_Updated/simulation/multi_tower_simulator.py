"""
Multi-Tower Simulator

Core simulation engine for battery and network dynamics across multiple towers.
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Import models - using absolute imports to avoid relative import issues
try:
    from models import UserPositioning
except ImportError:
    # Fallback for when run as module
    from ..models import UserPositioning


class MultiTowerSimulator:
    """
    Multi-tower battery and network simulator.

    Runs time-stepped simulation across all towers, computing power consumption,
    battery depletion, and load distribution each time step.
    """

    def __init__(
        self,
        config,
        env,
        user_model,
        coverage_model,
        terrain_model,
        battery_models,
        layout,
        load_model,
    ):
        """
        Initialize simulator.

        Args:
            config: Configuration dictionary (SIM_CONFIG)
            env: TemperatureModel instance
            user_model: UserModel instance
            coverage_model: CoverageModel instance
            terrain_model: TerrainModel instance
            battery_models: List of BatteryModel instances (one per tower)
            layout: TowerLayout instance
            load_model: LoadSharingModel instance
        """
        self.cfg = config
        self.env = env
        self.user_model = user_model
        self.coverage = coverage_model
        self.terrain = terrain_model
        self.batteries = battery_models
        self.layout = layout
        self.load_model = load_model
        self.user_positioning = UserPositioning(config["grid_size"])



    def run(self):
        """
        Execute full simulation.

        Returns:
            DataFrame with columns:
                - datetime
                - tower_id
                - x_m, y_m (position)
                - temperature_degC
                - effective_users
                - coverage_radius_m
                - coverage_load
                - tx_power_W
                - power_consumption_W
                - battery_soc_percent
        """
        dt = self.cfg["time_step_minutes"]
        steps = int(self.cfg["sim_days"] * 24 * 60 / dt)

        start = datetime.strptime(self.cfg["start_datetime"], "%Y-%m-%d %H:%M:%S")

        positions = self.layout.get_positions()

        rows = []

        for step in range(steps):
            time = start + timedelta(minutes=step * dt)
            hour = time.hour + time.minute / 60

            temp = round(self.env.value(hour), 2)

            total_users = max(self.user_model.users(hour) + np.random.normal(0, 5), 0)

            terrain_factors = [self.terrain.factor() for _ in positions]
            radii = np.array([self.coverage.radius(tf) for tf in terrain_factors])

            eff_users = self.user_positioning.assign_users_to_towers(total_users, positions, radii)

            for i, (x, y) in enumerate(positions):
                terrain_factor = terrain_factors[i]
                radius = round(radii[i], 2)

                cov_load = round(
                    self.coverage.load_factor(eff_users[i], radius), 2
                )

                tx_power = round(self.cfg["base_tx_power"] * terrain_factor, 2)

                power = round(
                    self.batteries[i].compute_power(
                        eff_users[i], tx_power, cov_load, temp
                    ),
                    2,
                )

                soc = round(self.batteries[i].update(power, dt / 60), 2)

                rows.append(
                    [time, i, x, y, temp, round(eff_users[i], 2), radius, cov_load, tx_power, power, soc]
                )

        df = pd.DataFrame(
            rows,
            columns=[
                "datetime",
                "tower_id",
                "x_m",
                "y_m",
                "temperature_degC",
                "effective_users",
                "coverage_radius_m",
                "coverage_load",
                "tx_power_W",
                "power_consumption_W",
                "battery_soc_percent",
            ],
        )

        return df