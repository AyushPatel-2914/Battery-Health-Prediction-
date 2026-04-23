"""Battery model used by Test simulation.

This class simulates how tower battery state of charge changes over time
based on idle draw, user demand, transmit power, coverage loading, and
temperature.
"""

import numpy as np

class BatteryModel:

    def __init__(self, capacity_Wh, idle_power, initial_soc):
        """Store battery capacity, idle power draw, and initial SOC."""
        self.capacity = capacity_Wh
        self.initial_capacity = capacity_Wh
        self.idle = idle_power
        self.soc = initial_soc
        self.hours_since_recharge = 0.0
        self.recharge_time_hours = np.random.uniform(2.0, 10.0)  # Random 2-10 hours
        self.inefficiency = max(0.85, np.random.normal(0.95, 0.05))
        self.measurement_noise = 0.9
        self.degradation_rate = np.random.uniform(0.0003, 0.0007)

    def compute_power(self, users, tx_power,
                      coverage_load, temperature):
        """Estimate current power draw using a simple physics-inspired model."""
        power = (
            self.idle
            + 0.35 * users
            + 0.0009 * tx_power**2
            + 2 * coverage_load
            + 0.03 * np.exp(temperature / 40)
        )
        return power

    def update(self, power, dt_hours):
        """Update internal SOC state based on power draw and elapsed time."""
        energy = power * dt_hours * self.inefficiency
        self.soc -= (energy / self.capacity) * 100
        self.soc = max(self.soc, 0)

        # Small capacity loss over time to simulate battery aging.
        self.capacity *= 1.0 - self.degradation_rate * dt_hours / 24.0
        self.capacity = max(self.capacity, 0.8 * self.initial_capacity)

        if self.soc == 0:
            self.hours_since_recharge += dt_hours
            if self.hours_since_recharge >= self.recharge_time_hours:
                self.soc = np.random.uniform(80.0, 100.0)
                self.hours_since_recharge = 0.0
                self.recharge_time_hours = np.random.uniform(2.0, 10.0)
        else:
            self.hours_since_recharge = 0.0

        reported_soc = self.soc + np.random.normal(0, self.measurement_noise)
        reported_soc = max(min(reported_soc, 100.0), 0.0)

        return round(reported_soc, 2)