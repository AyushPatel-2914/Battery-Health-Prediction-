import numpy as np

class CoverageModel:

    def __init__(self, base_radius):

        self.base_radius = base_radius

    def radius(self, terrain_factor):

        return self.base_radius * terrain_factor

    def load_factor(self, users, radius):

        area = np.pi * radius**2

        density = users / area

        return density * 1000   # scaling