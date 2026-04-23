"""Coverage model used by Test simulation."""

import numpy as np

class CoverageModel:

    def __init__(self, base_radius):
        """Store the base radio coverage radius."""
        self.base_radius = base_radius

    def radius(self, terrain_factor):
        """Return the effective coverage radius after terrain adjustment."""
        return self.base_radius * terrain_factor

    def load_factor(self, users, radius):
        """Compute a simple coverage load metric based on user density."""
        area = np.pi * radius**2
        density = users / area
        return density * 1000   # scale to a more convenient range