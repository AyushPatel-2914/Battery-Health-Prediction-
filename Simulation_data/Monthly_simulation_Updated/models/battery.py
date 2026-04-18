"""
Battery Model

Simulates battery state of charge, power consumption, and charging dynamics.
"""

import numpy as np


class BatteryModel:
    """Battery model with electro-thermal dynamics and auto-recharge."""

    def __init__(self, capacity_Wh, idle_power, initial_soc):
        """
        Initialize battery.

        Args:
            capacity_Wh: Battery capacity in Watt-hours
            idle_power: Base idle power consumption in Watts
            initial_soc: Initial state of charge (0-100%)
        """
        self.capacity = capacity_Wh
        self.idle = idle_power
        self.soc = initial_soc
        self.hours_since_recharge = 0.0
        self.recharge_time_hours = np.random.uniform(2.0, 10.0)

    def compute_power(self, users, tx_power, coverage_load, temperature):
        """
        Compute total power consumption.

        Power = idle + user_load + tx_power_loss + coverage_loss + thermal_stress

        Args:
            users: Number of effective users
            tx_power: Transmission power in Watts
            coverage_load: Coverage load factor
            temperature: Ambient temperature in Celsius

        Returns:
            Total power consumption in Watts
        """
        power = (
            self.idle
            + 0.35 * users
            + 0.0009 * tx_power**2
            + 2 * coverage_load
            + 0.03 * np.exp(temperature / 40)
        )
        return power

    def update(self, power, dt_hours):
        """
        Update battery state after time step.

        Args:
            power: Power consumption in Watts
            dt_hours: Time step in hours

        Returns:
            Updated SOC percentage
        """
        energy = power * dt_hours
        self.soc -= (energy / self.capacity) * 100
        self.soc = max(self.soc, 0)

        if self.soc == 0:
            self.hours_since_recharge += dt_hours
            if self.hours_since_recharge >= self.recharge_time_hours:
                self.soc = 100.0
                self.hours_since_recharge = 0.0
                self.recharge_time_hours = np.random.uniform(2.0, 10.0)
        else:
            self.hours_since_recharge = 0.0

        return self.soc
