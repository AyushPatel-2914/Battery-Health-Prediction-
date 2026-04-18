"""
Terrain Models

Simulates terrain effects and tower placement.
"""

import os
import pickle
import numpy as np
from .positioning import TowerPositioning


class TerrainModel:
    """Terrain factor model with random variation."""

    def __init__(self, base_factor=1.0, noise_scale=0.1):
        """
        Initialize terrain model.

        Args:
            base_factor: Base terrain multiplier
            noise_scale: Standard deviation of Gaussian noise
        """
        self.base = base_factor
        self.noise = noise_scale

    def factor(self):
        """
        Get terrain factor for current location.

        Returns:
            Terrain factor (typical range 0.8-1.3)
        """
        noise = np.random.normal(0, self.noise)
        return self.base * (1 + noise)


class TowerLayout:
    """Tower placement strategy - delegates to TowerPositioning."""

    def __init__(self, n_towers, grid_size):
        """
        Initialize tower layout.

        Args:
            n_towers: Number of towers to place
            grid_size: Size of grid for random placement
        """
        self.positioning = TowerPositioning(n_towers, grid_size)

    def generate_positions(self):
        """
        Generate tower positions using TowerPositioning.

        Returns:
            List of (x, y) tuples for tower positions
        """
        return self.positioning.get_positions()

    def get_positions(self):
        """Get tower positions."""
        return self.positioning.get_positions()

    def get_route_positions(self):
        """Get MAP track route (if available)."""
        return self.positioning.get_route_positions()
