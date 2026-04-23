"""Simulator for multi-tower scenarios in Test."""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

from terrain.terrain_surface import project_to_surface

class MultiTowerSimulator:

    def __init__(self,
                 config,
                 env,
                 user_model,
                 coverage_model,
                 terrain_model,
                 battery_models,
                 layout,
                 load_model):
        """Store all models and configuration required for simulation."""

        self.cfg = config
        self.env = env
        self.user_model = user_model
        self.coverage = coverage_model
        self.terrain = terrain_model
        self.batteries = battery_models
        self.layout = layout
        self.load_model = load_model

    def _sample_user_positions(self, user_count):
        """Sample realistic user positions along the MAP track or uniformly as fallback."""
        route_positions = self.layout.get_route_positions()
        if route_positions is None or len(route_positions) == 0:
            return np.random.uniform(
                0, self.cfg["grid_size"],
                size=(user_count, 2)
            )

        route_points = np.array(route_positions)
        indices = np.random.choice(len(route_points), size=user_count, replace=True)
        user_positions = route_points[indices].astype(float)

        jitter = np.random.normal(scale=15.0, size=(user_count, 2))
        return user_positions + jitter

    def _generate_daily_user_positions(self):
        """Generate representative user positions for the day for tower repositioning."""
        sample_hours = [6, 12, 18]  # Morning, noon, evening
        all_positions = []

        for hour in sample_hours:
            total_users = max(self.user_model.users(hour) + np.random.normal(0, 12), 0)
            user_count = int(round(total_users))

            if user_count > 0:
                day_positions = self._sample_user_positions(user_count)
                all_positions.extend(day_positions.tolist())

        return all_positions if all_positions else None

    def _assign_users_to_nearest_towers(self, total_users, positions, radii):
        """Assign users to the nearest tower inside each coverage radius."""
        positions_arr = np.array(positions)
        tower_count = len(positions_arr)
        effective_users = np.zeros(tower_count)

        if total_users <= 0 or tower_count == 0:
            return effective_users

        user_count = int(round(total_users))
        if user_count == 0:
            return effective_users

        user_positions = self._sample_user_positions(user_count)

        distances = np.linalg.norm(
            user_positions[:, None, :] - positions_arr[None, :, :],
            axis=2
        )

        masked = np.where(distances <= radii[None, :], distances, np.inf)
        nearest_indices = masked.argmin(axis=1)
        nearest_distances = masked.min(axis=1)

        valid = nearest_distances != np.inf
        for idx in nearest_indices[valid]:
            effective_users[idx] += 1

        return effective_users

    def run(self):
        """Run the multi-tower simulation and return the results DataFrame."""

        dt = self.cfg["time_step_minutes"]
        steps = int(self.cfg["sim_days"] * 24 * 60 / dt)

        start = datetime.strptime(
            self.cfg["start_datetime"],
            "%Y-%m-%d %H:%M:%S"
        )

        positions = self.layout.get_positions()
        positions_3d = project_to_surface(np.array(positions))
        z_coords = positions_3d[:, 2]

        rows = []
        current_date = None

        for step in range(steps):

            time = start + timedelta(minutes=step*dt)
            date = time.date()

            # Reposition towers daily using k-means clustering
            if date != current_date:
                current_date = date
                # Generate user positions for the day to determine optimal tower placement
                daily_user_positions = self._generate_daily_user_positions()
                if daily_user_positions:
                    old_positions = positions.copy()
                    positions = self.layout.reposition_towers_kmeans(daily_user_positions)
                    positions_3d = project_to_surface(np.array(positions))
                    z_coords = positions_3d[:, 2]
                    print(f"Date {date}: Towers repositioned using k-means clustering")

            hour = time.hour + time.minute/60

            temp = round(self.env.value(hour), 2)

            total_users = max(self.user_model.users(hour)
                              + np.random.normal(0, 12), 0)

            terrain_factors = [self.terrain.factor() for _ in positions]
            radii = np.array([
                self.coverage.radius(tf)
                for tf in terrain_factors
            ])

            eff_users = self._assign_users_to_nearest_towers(
                total_users,
                positions,
                radii
            )
            eff_users = self.load_model.distribute(eff_users, positions, self.batteries)
            eff_users = np.maximum(eff_users, 0.0)

            for i, (x, y) in enumerate(positions):

                terrain_factor = terrain_factors[i]
                radius = round(radii[i], 2)

                cov_load = round(
                    self.coverage.load_factor(
                        eff_users[i],
                        radius) * (1 + np.random.normal(0, 0.05)), 2)

                tx_power = round(
                    self.cfg["base_tx_power"]
                    * terrain_factor
                    * (1 + np.random.normal(0, 0.04)), 2)

                event_boost = 1.0
                if np.random.rand() < self.cfg.get("event_spike_probability", 0.035):
                    event_boost += np.random.uniform(0.12, 0.24)

                power = round(
                    self.batteries[i].compute_power(
                        eff_users[i],
                        tx_power,
                        cov_load,
                        temp) * event_boost,
                        2)

                soc = round(
                    self.batteries[i].update(
                        power,
                        dt/60), 2)

                rows.append([
                    time,
                    i,
                    x,
                    y,
                    round(z_coords[i], 2),
                    temp,
                    round(eff_users[i], 2),
                    radius,
                    cov_load,
                    tx_power,
                    power,
                    soc
                ])

        df = pd.DataFrame(rows, columns=[
            "datetime",
            "tower_id",
            "x_m",
            "y_m",
            "z_m",
            "temperature_degC",
            "effective_users",
            "coverage_radius_m",
            "coverage_load",
            "tx_power_W",
            "power_consumption_W",
            "battery_soc_percent"
        ])

        return df