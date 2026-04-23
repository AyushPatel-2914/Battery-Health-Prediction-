"""Single-day simulator used by Test for baseline tower behavior."""

import pandas as pd
from datetime import datetime, timedelta

class SingleDaySimulator:

    def __init__(self, config,
                 env,
                 user_model,
                 coverage_model,
                 terrain,
                 battery):
        """Initialize the single-day simulator with required models."""

        self.config = config
        self.env = env
        self.users = user_model
        self.coverage = coverage_model
        self.terrain = terrain
        self.battery = battery

    def run(self):
        """Run simulation for a single 24-hour period and return a DataFrame."""

        dt = self.config["time_step_minutes"]
        steps = int(24*60/dt)

        start = datetime.strptime(
            self.config["start_datetime"],
            "%Y-%m-%d %H:%M:%S"
        )

        rows = []

        for step in range(steps):

            current_time = start + timedelta(minutes=step*dt)

            hour = current_time.hour + current_time.minute/60

            temperature = round(self.env.value(hour), 2)

            users = round(self.users.users(hour), 2)

            terrain_factor = self.terrain.factor()

            radius = round(
                self.coverage.radius(terrain_factor), 2
            )

            coverage_load = round(
                self.coverage.load_factor(users, radius), 2
            )

            tx_power = round(
                self.config["base_tx_power"] * terrain_factor,
                2
            )

            power = round(
                self.battery.compute_power(
                    users,
                    tx_power,
                    coverage_load,
                    temperature
                ),
                2
            )

            soc = round(
                self.battery.update(power, dt/60),
                2
            )

            rows.append([
                current_time,
                temperature,
                users,
                radius,
                coverage_load,
                tx_power,
                power,
                soc
            ])

        df = pd.DataFrame(rows, columns=[
            "datetime",
            "temperature_degC",
            "active_users",
            "coverage_radius_m",
            "coverage_load",
            "tx_power_W",
            "power_consumption_W",
            "battery_soc_percent"
        ])

        return df