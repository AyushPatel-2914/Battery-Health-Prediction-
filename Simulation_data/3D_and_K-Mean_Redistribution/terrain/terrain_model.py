"""Simple terrain model used by Test simulation."""

import numpy as np

class TerrainModel:

    def __init__(self, base_factor=1.0, noise_scale=0.1):
        """Initialize terrain influence with a base factor and noise."""
        self.base = base_factor
        self.noise = noise_scale

    def factor(self):
        """Return a small terrain multiplier used to adjust coverage and power."""
        noise = np.random.normal(0, self.noise)
        return self.base * (1 + noise)
