"""
Animation and Visualization for Monthly Simulation
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os
import pickle

# Import models - using absolute imports to avoid relative import issues
try:
    from models import UserPositioning
except ImportError:
    # Fallback for when run as module
    from ..models import UserPositioning


def load_map_track():
    """Load the full MAP waypoint track data."""
    map_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "MAP"))
    if not os.path.isdir(map_dir):
        return None

    waypoints_path = os.path.join(map_dir, "waypoints.pkl")
    if not os.path.exists(waypoints_path):
        return None

    try:
        with open(waypoints_path, "rb") as f:
            waypoints_map = pickle.load(f)
        # Concatenate all waypoint chains into one track
        all_waypoints = []
        for chain_waypoints in waypoints_map.values():
            all_waypoints.extend(chain_waypoints)
        return np.array(all_waypoints) if all_waypoints else None
    except Exception:
        return None


def build_time_series(df):
    """Convert simulation DataFrame to time series pivots."""
    df_sorted = df.sort_values("datetime")
    load_pivot = df_sorted.pivot(index="datetime", columns="tower_id", values="effective_users").fillna(0)
    battery_pivot = df_sorted.pivot(index="datetime", columns="tower_id", values="battery_soc_percent").fillna(0)
    return load_pivot, battery_pivot





def animate_monthly_simulation(df, layout, sim_config=None):
    """
    Animate monthly simulation with towers and users on MAP track.

    Args:
        df: Simulation DataFrame
        layout: TowerLayout instance
        sim_config: Configuration dict (optional, for display_users)
    """
    # Load MAP track data
    map_track = load_map_track()
    tower_positions = np.array(layout.get_positions())

    load_ts, battery_ts = build_time_series(df)
    step_count = min(30, len(load_ts))  # Reduced from 180 to 30 for faster generation
    sample_indices = np.linspace(0, len(load_ts) - 1, step_count, dtype=int)
    sample_times = load_ts.index[sample_indices]
    sample_load = load_ts.iloc[sample_indices].values
    sample_battery = battery_ts.iloc[sample_indices].values

    display_users = sim_config.get("display_users", 50) if sim_config else 50
    user_positioning = UserPositioning(sim_config.get("grid_size", 1000) if sim_config else 1000)
    user_trajs = user_positioning.generate_user_positions_for_animation(map_track, display_users, step_count)

    fig, axs = plt.subplots(1, 3, figsize=(18, 6), gridspec_kw={"width_ratios": [2, 1, 1]})
    ax_map, ax_load, ax_battery = axs

    ax_load.set_ylim(0, max(10, sample_load.max() * 1.2))
    ax_load.set_title("Tower Effective Users")
    ax_load.set_xlabel("Tower ID")
    ax_load.set_ylabel("Effective Users")

    ax_battery.set_ylim(0, 110)
    ax_battery.set_title("Battery SOC (%)")
    ax_battery.set_xlabel("Tower ID")

    # Calculate map bounds
    if map_track is not None and len(map_track) > 0:
        track_min = map_track.min(axis=0)
        track_max = map_track.max(axis=0)
        has_track = True
    else:
        track_min = tower_positions.min(axis=0)
        track_max = tower_positions.max(axis=0)
        has_track = False

    pad = 50
    ax_map.set_xlim(track_min[0] - pad, track_max[0] + pad)
    ax_map.set_ylim(track_min[1] - pad, track_max[1] + pad)

    def update(frame):
        ax_map.clear()
        ax_load.clear()
        ax_battery.clear()

        current_time = sample_times[frame]
        loads = sample_load[frame]
        battery_vals = sample_battery[frame]
        user_positions = user_trajs[frame]

        # Draw MAP track
        if has_track and map_track is not None:
            ax_map.plot(
                map_track[:, 0],
                map_track[:, 1],
                color="gray",
                linewidth=1.5,
                alpha=0.5,
                label="Route Track",
            )

        # Towers stay static
        ax_map.scatter(
            tower_positions[:, 0],
            tower_positions[:, 1],
            marker="^",
            s=120,
            color="blue",
            edgecolors="black",
            zorder=5,
            label="Towers",
        )

        # Users move dynamically on track
        ax_map.scatter(
            user_positions[:, 0],
            user_positions[:, 1],
            c="red",
            s=30,
            alpha=0.8,
            edgecolors="black",
            zorder=4,
            label="Users",
        )

        ax_map.set_xlim(track_min[0] - pad, track_max[0] + pad)
        ax_map.set_ylim(track_min[1] - pad, track_max[1] + pad)
        ax_map.set_title("Monthly Simulation | Towers (Static) & Users (Dynamic on Track)")
        ax_map.legend(loc="upper right", fontsize=8)
        ax_map.text(
            0.02,
            0.95,
            f"Time: {current_time.strftime('%Y-%m-%d %H:%M')}",
            transform=ax_map.transAxes,
            fontsize=12,
            va="top",
        )

        ax_load.bar(range(len(tower_positions)), loads, color="skyblue")
        ax_load.set_ylim(0, max(10, sample_load.max() * 1.2))
        ax_load.set_title("Tower Effective Users")
        ax_load.set_xlabel("Tower ID")

        ax_battery.bar(range(len(tower_positions)), battery_vals, color="lightgreen")
        ax_battery.set_ylim(0, 110)
        ax_battery.set_title("Battery SOC (%)")
        ax_battery.set_xlabel("Tower ID")

    # Instead of animation, save a static visualization of the final state
    print("📊 Generating static visualization...")
    
    # Set up the plot with final state data
    final_loads = sample_load[-1]  # Last frame data
    final_battery = sample_battery[-1]
    final_time = sample_times[-1]
    
    # Clear and redraw with final data
    ax_map.clear()
    ax_load.clear()
    ax_battery.clear()
    
    # Draw MAP track
    if has_track and map_track is not None:
        ax_map.plot(
            map_track[:, 0],
            map_track[:, 1],
            color="gray",
            linewidth=1.5,
            alpha=0.5,
            label="Route Track",
        )

    # Towers
    ax_map.scatter(
        tower_positions[:, 0],
        tower_positions[:, 1],
        marker="^",
        s=120,
        color="blue",
        edgecolors="black",
        zorder=5,
        label="Towers",
    )

    # Final user positions
    final_user_positions = user_trajs[-1]
    ax_map.scatter(
        final_user_positions[:, 0],
        final_user_positions[:, 1],
        c="red",
        s=30,
        alpha=0.8,
        edgecolors="black",
        zorder=4,
        label="Users (Final)",
    )

    ax_map.set_xlim(track_min[0] - pad, track_max[0] + pad)
    ax_map.set_ylim(track_min[1] - pad, track_max[1] + pad)
    ax_map.set_title("Monthly Simulation - Final State")
    ax_map.legend(loc="upper right", fontsize=8)
    ax_map.text(
        0.02,
        0.95,
        f"Final Time: {final_time.strftime('%Y-%m-%d %H:%M')}",
        transform=ax_map.transAxes,
        fontsize=12,
        va="top",
    )

    # Load and battery bars
    ax_load.bar(range(len(tower_positions)), final_loads, color="skyblue")
    ax_load.set_ylim(0, max(10, sample_load.max() * 1.2))
    ax_load.set_title("Tower Effective Users")
    ax_load.set_xlabel("Tower ID")

    ax_battery.bar(range(len(tower_positions)), final_battery, color="lightgreen")
    ax_battery.set_ylim(0, 110)
    ax_battery.set_title("Battery SOC (%)")
    ax_battery.set_xlabel("Tower ID")

    plt.tight_layout()
    
    # Save static plot
    output_file = os.path.join(os.path.dirname(__file__), "..", "scripts", "data", "outputs", "monthly_simulation_final.png")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    fig.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close(fig)  # Clean up
    
    print(f"✅ Static visualization saved to: {output_file}")
    print("   (Shows towers, users, and final battery/load state)")
