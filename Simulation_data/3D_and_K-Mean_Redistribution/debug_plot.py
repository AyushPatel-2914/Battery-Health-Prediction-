import numpy as np
from utils.map_utils import load_map_track
from terrain.terrain_surface import build_surface_grid
from config.simulation_config import SIM_CONFIG

track = load_map_track()
print('track type', type(track), 'shape', None if track is None else track.shape)
print('grid_size', SIM_CONFIG['grid_size'])

if track is not None:
    print('track head', track[:5])
    print('track min', track.min(axis=0), 'max', track.max(axis=0))

X, Y, Z = build_surface_grid(track if track is not None else np.zeros((0, 2)), SIM_CONFIG['grid_size'], pad=50, resolution=120)
print('X range', X.min(), X.max())
print('Y range', Y.min(), Y.max())
print('Z range', Z.min(), Z.max())
print('X shape', X.shape, 'Y shape', Y.shape, 'Z shape', Z.shape)
