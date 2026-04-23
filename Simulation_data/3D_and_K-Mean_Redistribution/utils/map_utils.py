"""Map helpers used by Test visualization.

This module loads route waypoints from the central MAP folder and
builds synthetic user trajectories along the route.
"""

import os
import pickle

import numpy as np


def load_map_track():
    """Load waypoint route data from the root MAP directory."""
    map_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'MAP')
    )
    if not os.path.isdir(map_dir):
        return None

    waypoints_path = os.path.join(map_dir, 'waypoints.pkl')
    if not os.path.exists(waypoints_path):
        return None

    try:
        with open(waypoints_path, 'rb') as f:
            waypoints_map = pickle.load(f)

        all_waypoints = []
        for chain_waypoints in waypoints_map.values():
            all_waypoints.extend(chain_waypoints)

        return np.array(all_waypoints) if all_waypoints else None
    except Exception:
        return None


def build_user_trajectories_on_track(track, num_users, n_frames):
    """Create a 3D trajectory array for users moving along the track."""
    if track is None or len(track) == 0:
        return np.zeros((n_frames, num_users, 2))

    track_length = len(track)
    user_pos = np.zeros((n_frames, num_users, 2))

    # Each user moves with their own speed and direction
    user_speeds = np.random.uniform(0.5, 2.0, size=num_users)
    user_directions = np.random.choice([-1, 1], size=num_users)
    user_starts = np.random.uniform(0, track_length, size=num_users)

    for frame in range(n_frames):
        for user_idx in range(num_users):
            pos = (
                user_starts[user_idx]
                + user_directions[user_idx] * user_speeds[user_idx] * frame
            ) % track_length
            idx = int(pos)
            user_pos[frame, user_idx] = track[idx]

    return user_pos
