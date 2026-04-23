"""Visualization helpers for the Test animation.

This module builds plots for tower loads, battery SOC, and user motion
on the terrain surface generated from the route track.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from config.simulation_config import SIM_CONFIG
from utils.data_utils import build_time_series
from utils.map_utils import build_user_trajectories_on_track, load_map_track
from terrain.terrain_surface import build_surface_grid, project_to_surface


def animate_monthly_simulation(df, layout):
    """Render a 3-panel animation of the Test monthly simulation."""
    map_track = load_map_track()
    tower_positions = np.array(layout.get_positions())

    # Prepare time-series data for load and battery tracking
    load_ts, battery_ts = build_time_series(df)
    step_count = min(180, len(load_ts))
    sample_indices = np.linspace(0, len(load_ts) - 1, step_count, dtype=int)
    sample_times = load_ts.index[sample_indices]
    sample_load = load_ts.iloc[sample_indices].values
    sample_battery = battery_ts.iloc[sample_indices].values

    display_users = SIM_CONFIG["display_users"]
    user_trajs = build_user_trajectories_on_track(map_track, display_users, step_count)

    fig = plt.figure(figsize=(22, 8))
    ax_map = fig.add_subplot(131, projection='3d')
    ax_load = fig.add_subplot(132)
    ax_battery = fig.add_subplot(133)

    plt.subplots_adjust(bottom=0.24, wspace=0.35)

    has_track = map_track is not None and len(map_track) > 0
    surface_pad = 50
    surface_resolution = 120
    surface_X, surface_Y, surface_Z = build_surface_grid(
        map_track if has_track else tower_positions,
        SIM_CONFIG["grid_size"],
        pad=surface_pad,
        resolution=surface_resolution,
    )

    track_3d = project_to_surface(map_track) if has_track else None
    tower_3d = project_to_surface(tower_positions)
    base_tower_3d = tower_3d.copy()
    base_track_3d = track_3d.copy() if track_3d is not None else None
    base_surface_Z = surface_Z.copy()

    z_min = surface_Z.min() - 0.5
    z_max = surface_Z.max() + 0.5
    z_margin = (z_max - z_min) * 0.08
    fixed_z_min = z_min - z_margin
    fixed_z_max = z_max + z_margin

    ax_load.set_ylim(0, max(10, sample_load.max() * 1.2))
    ax_load.set_title('Tower Effective Users')
    ax_load.set_xlabel('Tower ID')
    ax_load.set_ylabel('Effective Users')

    ax_battery.set_ylim(0, 110)
    ax_battery.set_title('Battery SOC (%)')
    ax_battery.set_xlabel('Tower ID')

    fixed_view_azim = 45
    fixed_view_elev = 35
    z_exaggeration = 1.8

    def update(frame):
        """Update the animation frame for map and bar plots."""
        ax_map.cla()
        ax_load.clear()
        ax_battery.clear()

        current_time = sample_times[frame]
        loads = sample_load[frame]
        battery_vals = sample_battery[frame]
        user_positions = user_trajs[frame]
        user_3d = project_to_surface(user_positions)

        z_scale = z_exaggeration
        scaled_surface_Z = base_surface_Z * z_scale
        scaled_tower_3d = base_tower_3d.copy()
        scaled_tower_3d[:, 2] *= z_scale
        scaled_track_3d = None
        if base_track_3d is not None:
            scaled_track_3d = base_track_3d.copy()
            scaled_track_3d[:, 2] *= z_scale
        scaled_user_3d = user_3d.copy()
        scaled_user_3d[:, 2] *= z_scale

        ax_map.plot_surface(
            surface_X,
            surface_Y,
            scaled_surface_Z,
            cmap='viridis',
            alpha=0.55,
            linewidth=0,
            antialiased=True,
            rcount=surface_resolution,
            ccount=surface_resolution,
        )
        ax_map.plot_surface(
            surface_X,
            surface_Y,
            np.full_like(scaled_surface_Z, 0.0),
            color='gold',
            alpha=0.12,
            linewidth=0,
        )

        if has_track and scaled_track_3d is not None:
            ax_map.plot(
                scaled_track_3d[:, 0],
                scaled_track_3d[:, 1],
                scaled_track_3d[:, 2],
                color='gray',
                linewidth=2,
                alpha=0.75,
                label='Route Track',
            )

        ax_map.scatter(
            scaled_tower_3d[:, 0],
            scaled_tower_3d[:, 1],
            scaled_tower_3d[:, 2],
            marker='^',
            s=100,
            color='blue',
            edgecolors='black',
            zorder=6,
            label='Towers',
        )
        ax_map.scatter(
            scaled_user_3d[:, 0],
            scaled_user_3d[:, 1],
            scaled_user_3d[:, 2],
            c='red',
            s=30,
            alpha=0.9,
            edgecolors='black',
            zorder=5,
            label='Users',
        )

        ax_map.set_title('3D Simulation Surface | Track Mapped onto Terrain')
        ax_map.set_xlabel('X')
        ax_map.set_ylabel('Y')
        ax_map.set_zlabel('Elevation')
        ax_map.set_xlim(surface_X.min(), surface_X.max())
        ax_map.set_ylim(surface_Y.min(), surface_Y.max())
        z_lower = scaled_surface_Z.min() - 0.8
        z_upper = scaled_surface_Z.max() + 0.8
        ax_map.set_zlim(z_lower, z_upper)
        ax_map.view_init(elev=fixed_view_elev, azim=fixed_view_azim)
        ax_map.legend(loc='upper right', fontsize=8)
        ax_map.set_box_aspect((1, 1, 0.25))
        ax_map.text2D(
            0.02,
            0.95,
            f"Time: {current_time.strftime('%Y-%m-%d %H:%M')}",
            transform=ax_map.transAxes,
            fontsize=10,
        )

        ax_load.bar(range(len(tower_positions)), loads, color='skyblue')
        ax_load.set_ylim(0, max(10, sample_load.max() * 1.2))
        ax_load.set_title('Tower Effective Users')
        ax_load.set_xlabel('Tower ID')

        ax_battery.bar(range(len(tower_positions)), battery_vals, color='lightgreen')
        ax_battery.set_ylim(0, 110)
        ax_battery.set_title('Battery SOC (%)')
        ax_battery.set_xlabel('Tower ID')

    ani = FuncAnimation(fig, update, frames=step_count, interval=200, repeat=False)
    plt.tight_layout()
    plt.show()
