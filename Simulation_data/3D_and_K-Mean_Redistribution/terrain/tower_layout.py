"""Tower layout helper for Test simulation.

This module chooses tower placements either from a saved MAP track
or randomly when MAP data is unavailable.
"""

import os
import pickle
import numpy as np

class TowerLayout:

    def __init__(self, n_towers, grid_size):
        """Initialize tower layout with the desired count and grid bounds."""
        self.n = n_towers
        self.grid = grid_size
        self.route_positions = None
        self.positions = self.generate_positions()

    def generate_positions(self):
        """Generate tower positions from the MAP route or randomly."""
        self.route_positions = self._load_map_route_positions()
        if self.route_positions is not None and len(self.route_positions) >= self.n:
            positions = self._sample_positions_along_route(self.route_positions, self.n)
            print(f"TowerLayout: using {len(positions)} MAP track positions.")
            return positions

        print("TowerLayout: using random tower positions (MAP track unavailable).")
        self.route_positions = None
        return self._generate_random_positions()

    def reposition_towers_kmeans(self, user_positions):
        """Reposition towers using k-means clustering on user positions, constrained to track."""
        if self.route_positions is None or len(self.route_positions) < self.n:
            # Fall back to random repositioning if no track available
            return self._generate_random_positions()

        if len(user_positions) == 0:
            return self.positions

        centroids = self._kmeans_clustering(user_positions, self.n)

        # Select unique track points closest to each centroid
        available_positions = [tuple(pos) for pos in self.route_positions]
        new_positions = []
        for centroid in centroids:
            chosen = self._find_closest_unique_track_position(centroid, available_positions)
            if chosen is None:
                break
            available_positions.remove(chosen)
            new_positions.append((round(float(chosen[0]), 2), round(float(chosen[1]), 2)))

        # If there are not enough unique points, fill with evenly sampled route positions
        if len(new_positions) < self.n:
            extra = self._sample_positions_along_route(self.route_positions, self.n - len(new_positions))
            for pos in extra:
                if pos not in new_positions:
                    new_positions.append(pos)
                if len(new_positions) >= self.n:
                    break

        self.positions = new_positions
        return self.positions

    def _kmeans_clustering(self, points, k, max_iters=10):
        """Simple k-means clustering implementation."""
        if len(points) < k:
            # If fewer points than clusters, use random positions
            return self._generate_random_positions()

        points = np.array(points)

        centroids = points[np.random.choice(len(points), k, replace=False)]

        for _ in range(max_iters):
            distances = np.linalg.norm(points[:, None] - centroids[None, :], axis=2)
            labels = np.argmin(distances, axis=1)

            new_centroids = np.array([
                points[labels == i].mean(axis=0) if np.any(labels == i)
                else points[np.random.choice(len(points))]
                for i in range(k)
            ])

            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids

        return centroids

    def _find_closest_unique_track_position(self, target_point, available_positions):
        """Pick the closest track position from the remaining available track points."""
        if not available_positions:
            return self._find_closest_track_position(target_point)

        target = np.array(target_point)
        track_points = np.array(available_positions)

        distances = np.linalg.norm(track_points - target, axis=1)
        closest_idx = np.argmin(distances)
        chosen = tuple(track_points[closest_idx])

        return chosen

    def _find_closest_track_position(self, target_point):
        """Find the closest position on the track to a target point."""
        if not self.route_positions:
            return target_point

        target = np.array(target_point)
        track_points = np.array(self.route_positions)

        distances = np.linalg.norm(track_points - target, axis=1)
        closest_idx = np.argmin(distances)

        return (round(float(track_points[closest_idx][0]), 2),
                round(float(track_points[closest_idx][1]), 2))

    def _generate_random_positions(self):
        """Generate random tower positions within the grid bounds."""
        pos = []
        for _ in range(self.n):
            x = np.random.uniform(0, self.grid)
            y = np.random.uniform(0, self.grid)
            pos.append((round(x, 2), round(y, 2)))
        return pos

    def _load_map_route_positions(self):
        """Load a saved MAP route from the top-level MAP directory."""
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

        all_waypoints = []
        for chain_waypoints in waypoints_map.values():
            if chain_waypoints:
                all_waypoints.extend(chain_waypoints)

        if not all_waypoints:
            return None

        return [tuple(point) for point in all_waypoints]

    def _sample_positions_along_route(self, route_points, count):
        """Sample a fixed number of positions evenly along the route."""
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
        """Return tower XY positions."""
        return self.positions

    def get_route_positions(self):
        """Return the MAP route positions used for placement, if available."""
        return self.route_positions
