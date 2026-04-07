import numpy as np

class BatteryModel:

    def __init__(self, capacity_Wh, idle_power, initial_soc):

        self.capacity = capacity_Wh
        self.idle = idle_power
        self.soc = initial_soc
        self.hours_since_recharge = 0.0
        self.recharge_time_hours = np.random.uniform(2.0, 10.0)  # Random 2-10 hours

    def compute_power(self, users, tx_power,
                      coverage_load, temperature):

        power = (
            self.idle
            + 0.35 * users
            + 0.0009 * tx_power**2
            + 2 * coverage_load
            + 0.03*np.exp(temperature/40)
        )

        return power

    def update(self, power, dt_hours):

        energy = power * dt_hours
        self.soc -= (energy / self.capacity) * 100
        self.soc = max(self.soc, 0)

        if self.soc == 0:
            self.hours_since_recharge += dt_hours
            if self.hours_since_recharge >= self.recharge_time_hours:
                self.soc = 100.0
                self.hours_since_recharge = 0.0
                # Set new random recharge time for next depletion
                self.recharge_time_hours = np.random.uniform(2.0, 10.0)
        else:
            self.hours_since_recharge = 0.0

        return self.soc