"""Environmental temperature model used by Test simulation."""

import numpy as np

class TemperatureModel:

    def __init__(self, season):
        """Set seasonal temperature parameters."""
        if season == "summer":
            self.mean = 38
            self.amp = 7
        elif season == "winter":
            self.mean = 20
            self.amp = 5
        else:
            self.mean = 30
            self.amp = 6

    def value(self, hour):
        """Return temperature at the given hour with daily variation and noise."""
        noise = np.random.normal(0, 0.5)
        temp = self.mean + self.amp * np.sin(
            2 * np.pi * (hour - 6) / 24
        ) + noise
        return temp
