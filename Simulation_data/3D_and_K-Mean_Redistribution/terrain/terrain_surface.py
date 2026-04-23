"""Terrain surface utilities for Test visualization."""

import numpy as np


def surface_height(x, y, amplitude=2.0, frequency=0.01, phase=0.0):
    """Return a plane surface height with smooth depressions at mining locations."""
    # Base plane surface
    base_height = np.zeros_like(x)

    # Mining pit centers (from helper.py data)
    pit_centers = [
        (-392.86, 250.0),   # FW pits
        (150.0, -258.33),   # N pits
        (600.0, -158.33),   # NE pits
        (150.0, 714.29)     # S pits
    ]

    # Create smooth depressions at each pit center
    for cx, cy in pit_centers:
        distance = np.sqrt((x - cx)**2 + (y - cy)**2)
        # Smooth depression with radius 220 (from helper.py) and depth based on proximity
        mask = distance < 220
        if np.any(mask):
            # Use a smooth function that goes from -depth at center to 0 at radius
            # Using a cosine function for smooth transition
            depression = np.zeros_like(distance)
            depression[mask] = -3.0 * (1 + np.cos(np.pi * distance[mask] / 220)) / 2
            base_height += depression

    return base_height


def build_surface_grid(track, grid_size, pad=50, resolution=120):
    """Build a terrain mesh around the track or tower extents."""
    if track is not None and len(track) > 0:
        track_min = track.min(axis=0)
        track_max = track.max(axis=0)
    else:
        track_min = np.array([0.0, 0.0])
        track_max = np.array([grid_size, grid_size])

    x = np.linspace(track_min[0] - pad, track_max[0] + pad, resolution)
    y = np.linspace(track_min[1] - pad, track_max[1] + pad, resolution)
    X, Y = np.meshgrid(x, y)
    Z = surface_height(X, Y)
    return X, Y, Z


def project_to_surface(points):
    """Lift 2D points onto the terrain surface for 3D plotting."""
    if points is None or len(points) == 0:
        return np.zeros((0, 3))
    zs = surface_height(points[:, 0], points[:, 1])
    return np.column_stack((points[:, 0], points[:, 1], zs))
