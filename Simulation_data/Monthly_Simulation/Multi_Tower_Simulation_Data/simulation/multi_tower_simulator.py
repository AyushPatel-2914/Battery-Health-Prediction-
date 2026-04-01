import pandas as pd
from datetime import datetime, timedelta
import numpy as np

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

        self.cfg = config
        self.env = env
        self.user_model = user_model
        self.coverage = coverage_model
        self.terrain = terrain_model
        self.batteries = battery_models
        self.layout = layout
        self.load_model = load_model

    def run(self):

        dt = self.cfg["time_step_minutes"]
        steps = int(self.cfg["sim_days"] * 24 * 60 / dt)

        start = datetime.strptime(
            self.cfg["start_datetime"],
            "%Y-%m-%d %H:%M:%S"
        )

        positions = self.layout.get_positions()

        rows = []

        for step in range(steps):

            time = start + timedelta(minutes=step*dt)

            hour = time.hour + time.minute/60

            temp = round(self.env.value(hour),2)

            base_users = []

            for _ in positions:
                base_users.append(
                    max(self.user_model.users(hour)
                        + np.random.normal(0,3), 0)
                )

            eff_users = self.load_model.distribute(
                base_users,
                positions,
                self.batteries  
            )

            for i, (x,y) in enumerate(positions):

                terrain_factor = self.terrain.factor()

                radius = round(
                    self.coverage.radius(terrain_factor),2)

                cov_load = round(
                    self.coverage.load_factor(
                        eff_users[i],
                        radius),2)

                tx_power = round(
                    self.cfg["base_tx_power"]
                    * terrain_factor,2)

                power = round(
                    self.batteries[i].compute_power(
                        eff_users[i],
                        tx_power,
                        cov_load,
                        temp),2)

                soc = round(
                    self.batteries[i].update(
                        power,
                        dt/60),2)

                rows.append([
                    time,
                    i,
                    x,
                    y,
                    temp,
                    round(eff_users[i],2),
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
            "temperature_degC",
            "effective_users",
            "coverage_radius_m",
            "coverage_load",
            "tx_power_W",
            "power_consumption_W",
            "battery_soc_percent"
        ])

        return df