import os
import sys
import pickle
import numpy as np

class TowerLayout:

    def __init__(self, n_towers, grid_size):
        self.n = n_towers
        self.grid = grid_size
        self.route_positions = None
        self.positions = self.generate_positions()

    def generate_positions(self):
        self.route_positions = self._load_map_route_positions()
        if self.route_positions is not None and len(self.route_positions) >= self.n:
            positions = self._sample_positions_along_route(self.route_positions, self.n)
            print(f"TowerLayout: using {len(positions)} MAP track positions.")
            return positions

        print("TowerLayout: using random tower positions (MAP track unavailable).")
        self.route_positions = None
        return self._generate_random_positions()

    def _generate_random_positions(self):
        pos = []
        for _ in range(self.n):
            x = np.random.uniform(0, self.grid)
            y = np.random.uniform(0, self.grid)
            pos.append((round(x, 2), round(y, 2)))
        return pos

    def _load_map_route_positions(self):
        """Load the full MAP track from waypoints.pkl"""
        map_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'MAP'))
        if not os.path.isdir(map_dir):
            return None

        waypoints_path = os.path.join(map_dir, 'waypoints.pkl')
        if not os.path.exists(waypoints_path):
            return None

        try:
            with open(waypoints_path, 'rb') as f:
                waypoints_map = pickle.load(f)
        except Exception:
            return None

        if not waypoints_map:
            return None

        # Concatenate all waypoint chains into a single track
        all_waypoints = []
        for chain_waypoints in waypoints_map.values():
            if chain_waypoints:
                all_waypoints.extend(chain_waypoints)

        if not all_waypoints:
            return None

        return [tuple(point) for point in all_waypoints]

    def _sample_positions_along_route(self, route_points, count):
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
        return self.positions

    def get_route_positions(self):
        return self.route_positions
