"""
Environment Model

Simulates environmental factors like temperature with seasonal variation.
"""

import numpy as np


class TemperatureModel:
    """Temperature model with daily and seasonal variation."""

    def __init__(self, season):
        """
        Initialize temperature model for given season.

        Args:
            season: One of "summer", "winter", or other (default mean)
        """
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
        """
        Get temperature for given hour of day.

        Temperature follows sinusoidal daily cycle with Gaussian noise.

        Args:
            hour: Hour of day (0-23.99)

        Returns:
            Temperature in Celsius
        """
        noise = np.random.normal(0, 0.5)
        temp = self.mean + self.amp * np.sin(2 * np.pi * (hour - 6) / 24) + noise
        return temp
