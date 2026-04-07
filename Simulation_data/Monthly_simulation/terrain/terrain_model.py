import numpy as np

class TerrainModel:

    def __init__(self, base_factor=1.0, noise_scale=0.1):
        self.base = base_factor
        self.noise = noise_scale

    def factor(self):
        # Add Gaussian noise to terrain factor
        noise = np.random.normal(0, self.noise)
        return self.base * (1 + noise)
