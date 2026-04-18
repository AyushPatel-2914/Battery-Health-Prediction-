"""
Positioning Module

Handles tower and user position allocation and assignment.
"""

import os
import pickle
import numpy as np


class TowerPositioning:
    """Handles tower position allocation and management."""

    def __init__(self, n_towers, grid_size):
        """
        Initialize tower positioning.

        Args:
            n_towers: Number of towers to place
            grid_size: Size of grid for random placement
        """
        self.n_towers = n_towers
        self.grid_size = grid_size
        self.route_positions = None
        self.tower_positions = self._generate_tower_positions()

    def _generate_tower_positions(self):
        """
        Generate tower positions, preferring MAP track if available.

        Returns:
            List of (x, y) tuples for tower positions
        """
        self.route_positions = self._load_map_route_positions()
        if self.route_positions is not None and len(self.route_positions) >= self.n_towers:
            positions = self._sample_positions_along_route(self.route_positions, self.n_towers)
            print(f"TowerPositioning: using {len(positions)} MAP track positions.")
            return positions

        print("TowerPositioning: using random tower positions (MAP track unavailable).")
        self.route_positions = None
        return self._generate_random_positions()

    def _generate_random_positions(self):
        """Generate random tower positions on grid."""
        positions = []
        for _ in range(self.n_towers):
            x = np.random.uniform(0, self.grid_size)
            y = np.random.uniform(0, self.grid_size)
            positions.append((round(x, 2), round(y, 2)))
        return positions

    def _load_map_route_positions(self):
        """Load MAP track from waypoints.pkl file."""
        map_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "MAP")
        )
        if not os.path.isdir(map_dir):
            return None

        waypoints_path = os.path.join(map_dir, "waypoints.pkl")
        if not os.path.exists(waypoints_path):
            return None

        try:
            with open(waypoints_path, "rb") as f:
                waypoints_map = pickle.load(f)
        except Exception:
            return None

        if not waypoints_map:
            return None

        all_waypoints = []
        for chain_waypoints in waypoints_map.values():
            if chain_waypoints:
                all_waypoints.extend(chain_waypoints)

        if not all_waypoints:
            return None

        return [tuple(point) for point in all_waypoints]

    def _sample_positions_along_route(self, route_points, count):
        """Sample evenly-spaced positions along route."""
        if len(route_points) <= count:
            return [
                (round(float(point[0]), 2), round(float(point[1]), 2))
                for point in route_points[:count]
            ]

        indices = np.linspace(0, len(route_points) - 1, count)
        positions = []
        for idx in indices:
            point = route_points[int(round(idx))]
            positions.append((round(float(point[0]), 2), round(float(point[1]), 2)))
        return positions

    def get_positions(self):
        """Get tower positions."""
        return self.tower_positions

    def get_route_positions(self):
        """Get MAP track route (if available)."""
        return self.route_positions


class UserPositioning:
    """Handles user position allocation and tower assignment."""

    def __init__(self, grid_size):
        """
        Initialize user positioning.

        Args:
            grid_size: Size of simulation grid
        """
        self.grid_size = grid_size

    def assign_users_to_towers(self, total_users, tower_positions, coverage_radii):
        """
        Assign users to nearest towers within coverage radius.

        Args:
            total_users: Total number of users in system
            tower_positions: List of (x, y) tuples for tower positions
            coverage_radii: Array of coverage radius per tower

        Returns:
            Array of user count per tower
        """
        tower_positions_arr = np.array(tower_positions)
        n_towers = len(tower_positions_arr)
        effective_users = np.zeros(n_towers)

        if total_users <= 0 or n_towers == 0:
            return effective_users

        user_count = int(round(total_users))
        if user_count == 0:
            return effective_users

        # Generate random user positions in grid
        user_positions = np.random.uniform(0, self.grid_size, size=(user_count, 2))

        # Calculate distances to all towers
        distances = np.linalg.norm(
            user_positions[:, None, :] - tower_positions_arr[None, :, :], axis=2
        )

        # Find nearest tower within coverage radius
        masked_distances = np.where(distances <= coverage_radii[None, :], distances, np.inf)
        nearest_indices = masked_distances.argmin(axis=1)
        nearest_distances = masked_distances.min(axis=1)

        # Count users per tower (only those within coverage)
        valid_assignments = nearest_distances != np.inf
        for tower_idx in nearest_indices[valid_assignments]:
            effective_users[tower_idx] += 1

        return effective_users

    def generate_user_positions_for_animation(self, track, num_users, n_frames):
        """
        Generate user trajectories for animation (moving on MAP track).

        Args:
            track: MAP track waypoints
            num_users: Number of users to show
            n_frames: Number of animation frames

        Returns:
            Array of shape (n_frames, num_users, 2) with user positions
        """
        if track is None or len(track) == 0:
            return np.zeros((n_frames, num_users, 2))

        track_length = len(track)
        user_positions = np.zeros((n_frames, num_users, 2))

        # Each user starts at random position and moves randomly on track
        user_speeds = np.random.uniform(0.5, 2.0, size=num_users)
        user_directions = np.random.choice([-1, 1], size=num_users)
        user_starts = np.random.uniform(0, track_length, size=num_users)

        for frame in range(n_frames):
            for user_idx in range(num_users):
                pos = (user_starts[user_idx] + user_directions[user_idx] * user_speeds[user_idx] * frame) % track_length
                idx = int(pos)
                user_positions[frame, user_idx] = track[idx]

        return user_positions