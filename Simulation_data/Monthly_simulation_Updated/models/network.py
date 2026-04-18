"""
Network Models

Simulates user demand, coverage, load distribution, and traffic patterns.
"""

import numpy as np


class UserModel:
    """User demand model with daily activity pattern."""

    def __init__(self, max_users, noise_scale=5.0):
        """
        Initialize user model.

        Args:
            max_users: Maximum concurrent users
            noise_scale: Standard deviation of Gaussian noise
        """
        self.max_users = max_users
        self.noise_scale = noise_scale

    def users(self, hour):
        """
        Get number of users for given hour.

        Usage follows sin^2 pattern with peak at 8 AM and low at night.

        Args:
            hour: Hour of day (0-23.99)

        Returns:
            Number of users (non-negative)
        """
        base = self.max_users * (0.25 + 0.75 * np.sin(2 * np.pi * (hour - 8) / 24) ** 2)
        noise = np.random.normal(0, self.noise_scale)
        users = base + noise
        return max(users, 0)


class CoverageModel:
    """Coverage and coverage load model."""

    def __init__(self, base_radius):
        """
        Initialize coverage model.

        Args:
            base_radius: Base coverage radius in meters
        """
        self.base_radius = base_radius

    def radius(self, terrain_factor):
        """
        Compute coverage radius given terrain factor.

        Args:
            terrain_factor: Terrain scaling factor (e.g., 0.8-1.3)

        Returns:
            Coverage radius in meters
        """
        return self.base_radius * terrain_factor

    def load_factor(self, users, radius):
        """
        Compute coverage load from user density.

        Args:
            users: Number of users in coverage area
            radius: Coverage radius in meters

        Returns:
            Normalized coverage load factor
        """
        area = np.pi * radius**2
        density = users / (area + 1e-6)  # Avoid division by zero
        return density * 1000


class LoadSharingModel:
    """Load redistribution based on battery SOC."""

    def __init__(self, decay=250):
        """
        Initialize load sharing model.

        Args:
            decay: Decay constant (unused in current implementation)
        """
        self.decay = decay

    def distribute(self, base_users, positions, batteries):
        """
        Redistribute users among towers based on SOC.

        Towers with higher SOC receive more load.

        Args:
            base_users: Array of base user counts per tower
            positions: Tower positions (unused in current implementation)
            batteries: BatteryModel objects for each tower

        Returns:
            Array of effective users per tower
        """
        base_users = np.array(base_users)
        socs = np.array([b.soc for b in batteries])
        capacity = socs / (np.sum(socs) + 1e-6)
        total_users = np.sum(base_users)
        effective_users = capacity * total_users
        return effective_users


class TrafficModel:
    """Traffic/load model with daily pattern and random bursts."""

    def __init__(self, peak):
        """
        Initialize traffic model.

        Args:
            peak: Peak traffic value
        """
        self.peak = peak

    def value(self, hour):
        """
        Get traffic value for given hour.

        Args:
            hour: Hour of day (0-23.99)

        Returns:
            Traffic value
        """
        base = self.peak * (0.3 + 0.7 * np.sin(2 * np.pi * (hour - 8) / 24) ** 2)
        burst = np.random.poisson(3)
        return base + burst
