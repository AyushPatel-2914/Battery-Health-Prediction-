import numpy as np

class TowerLayout:

    def __init__(self, n_towers, grid_size):

        self.n = n_towers
        self.grid = grid_size

        self.positions = self.generate_positions()

    def generate_positions(self):

        pos = []

        for _ in range(self.n):
            x = np.random.uniform(0, self.grid)
            y = np.random.uniform(0, self.grid)
            pos.append((round(x,2), round(y,2)))

        return pos

    def get_positions(self):
        return self.positions