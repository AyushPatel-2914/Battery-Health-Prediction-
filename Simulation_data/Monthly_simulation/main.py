import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os
import shutil

from config.simulation_config import SIM_CONFIG

from environment.temperature_model import TemperatureModel
from network.user_model import UserModel
from network.coverage_model import CoverageModel
from terrain.terrain_model import TerrainModel
from terrain.tower_layout import TowerLayout
from network.load_sharing_model import LoadSharingModel
from battery.battery_model import BatteryModel
from simulation.multi_tower_simulator import MultiTowerSimulator


def build_time_series(df):
    df_sorted = df.sort_values('datetime')
    load_pivot = df_sorted.pivot(index='datetime', columns='tower_id', values='effective_users').fillna(0)
    battery_pivot = df_sorted.pivot(index='datetime', columns='tower_id', values='battery_soc_percent').fillna(0)
    return load_pivot, battery_pivot


def load_map_track():
    """Load the full MAP waypoint track data."""
    import os
    import sys
    import pickle
    
    map_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'MAP'))
    if not os.path.isdir(map_dir):
        return None
    
    waypoints_path = os.path.join(map_dir, 'waypoints.pkl')
    if not os.path.exists(waypoints_path):
        return None
    
    try:
        with open(waypoints_path, 'rb') as f:
            waypoints_map = pickle.load(f)
        # Concatenate all waypoint chains into one track
        all_waypoints = []
        for chain_waypoints in waypoints_map.values():
            all_waypoints.extend(chain_waypoints)
        return np.array(all_waypoints) if all_waypoints else None
    except Exception:
        return None


def build_user_trajectories_on_track(track, num_users, n_frames):
    """Generate user trajectories randomly moving on the track."""
    if track is None or len(track) == 0:
        return np.zeros((n_frames, num_users, 2))
    
    track_length = len(track)
    user_pos = np.zeros((n_frames, num_users, 2))
    
    # Each user starts at a random position and moves randomly on the track
    user_speeds = np.random.uniform(0.5, 2.0, size=num_users)
    user_directions = np.random.choice([-1, 1], size=num_users)  # Forward or backward
    user_starts = np.random.uniform(0, track_length, size=num_users)
    
    for frame in range(n_frames):
        for user_idx in range(num_users):
            # Position on track with wrap-around
            pos = (user_starts[user_idx] + user_directions[user_idx] * user_speeds[user_idx] * frame) % track_length
            idx = int(pos)
            user_pos[frame, user_idx] = track[idx]
    
    return user_pos


def animate_monthly_simulation(df, layout):
    # Load MAP track data
    map_track = load_map_track()
    tower_positions = np.array(layout.get_positions())

    load_ts, battery_ts = build_time_series(df)
    step_count = min(180, len(load_ts))
    sample_indices = np.linspace(0, len(load_ts) - 1, step_count, dtype=int)
    sample_times = load_ts.index[sample_indices]
    sample_load = load_ts.iloc[sample_indices].values
    sample_battery = battery_ts.iloc[sample_indices].values

    display_users = SIM_CONFIG["display_users"]
    user_trajs = build_user_trajectories_on_track(map_track, display_users, step_count)

    fig, axs = plt.subplots(1, 3, figsize=(18, 6), gridspec_kw={'width_ratios': [2, 1, 1]})
    ax_map, ax_load, ax_battery = axs

    ax_load.set_ylim(0, max(10, sample_load.max() * 1.2))
    ax_load.set_title('Tower Effective Users')
    ax_load.set_xlabel('Tower ID')
    ax_load.set_ylabel('Effective Users')

    ax_battery.set_ylim(0, 110)
    ax_battery.set_title('Battery SOC (%)')
    ax_battery.set_xlabel('Tower ID')

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
            ax_map.plot(map_track[:, 0], map_track[:, 1], color='gray', linewidth=1.5, alpha=0.5, label='Route Track')

        # Towers stay static
        ax_map.scatter(tower_positions[:, 0], tower_positions[:, 1], marker='^', s=120, color='blue', edgecolors='black', zorder=5, label='Towers')
        
        # Users move dynamically on track
        ax_map.scatter(user_positions[:, 0], user_positions[:, 1], c='red', s=30, alpha=0.8, edgecolors='black', zorder=4, label='Users')

        ax_map.set_xlim(track_min[0] - pad, track_max[0] + pad)
        ax_map.set_ylim(track_min[1] - pad, track_max[1] + pad)
        ax_map.set_title('Monthly Simulation | Towers (Static) & Users (Dynamic on Track)')
        ax_map.legend(loc='upper right', fontsize=8)
        ax_map.text(0.02, 0.95, f"Time: {current_time.strftime('%Y-%m-%d %H:%M')}", transform=ax_map.transAxes, fontsize=12, va='top')

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


# ---------- FORCE 2 TOWERS ----------
#SIM_CONFIG["num_towers"] = 2

# NOTE: Do not override config values here if you want edits in config to take effect.
#SIM_CONFIG["sim_days"] = 30


# ---------- ADD GAUSSIAN NOISE TO SIMULATION PARAMETERS ----------
print("🔧 Adding Gaussian noise to simulation parameters...")

# Create noisy config copy
noisy_config = SIM_CONFIG.copy()

# Add noise to battery parameters (5% std dev)
battery_noise = 0.05
noisy_config["battery_capacity_Wh"] = SIM_CONFIG["battery_capacity_Wh"] * (1 + np.random.normal(0, battery_noise))
noisy_config["idle_power"] = SIM_CONFIG["idle_power"] * (1 + np.random.normal(0, battery_noise))

# Add noise to coverage parameters (3% std dev)
coverage_noise = 0.03
noisy_config["base_coverage_radius"] = SIM_CONFIG["base_coverage_radius"] * (1 + np.random.normal(0, coverage_noise))

# Add noise to power parameters (5% std dev)
power_noise = 0.05
noisy_config["base_tx_power"] = SIM_CONFIG["base_tx_power"] * (1 + np.random.normal(0, power_noise))

print(f"   Battery parameters noise: {battery_noise*100}%")
print(f"   Coverage radius noise: {coverage_noise*100}%")
print(f"   TX power noise: {power_noise*100}%")


# ---------- CREATE OBJECTS ----------

env = TemperatureModel(
    SIM_CONFIG["season"]
)

user_model = UserModel(
    SIM_CONFIG["max_users"],
    noise_scale=7.0  # Increased noise for more variation
)

coverage_model = CoverageModel(
    noisy_config["base_coverage_radius"]
)

terrain = TerrainModel(base_factor=1.0, noise_scale=0.1)

layout = TowerLayout(
    SIM_CONFIG["num_towers"],
    SIM_CONFIG["grid_size"]
)

load_model = LoadSharingModel()

batteries = [
    BatteryModel(
        noisy_config["battery_capacity_Wh"],
        noisy_config["idle_power"],
        SIM_CONFIG["initial_soc"]
    )
    for _ in range(SIM_CONFIG["num_towers"])
]


# ---------- RUN SIMULATION ----------

sim = MultiTowerSimulator(
    SIM_CONFIG,
    env,
    user_model,
    coverage_model,
    terrain,
    batteries,
    layout,
    load_model
)

df = sim.run()


# ---------- SAVE CSV (MONTH DATA) ----------

SIM_DATA_DIR = os.path.join(os.path.dirname(__file__), "simulation_data")
os.makedirs(SIM_DATA_DIR, exist_ok=True)

if os.path.exists(SIM_DATA_DIR):
    shutil.rmtree(SIM_DATA_DIR)
    os.makedirs(SIM_DATA_DIR)

for tid in df["tower_id"].unique():

    tower_df = df[df["tower_id"] == tid]

    filename = os.path.join(SIM_DATA_DIR, f"tower_{tid}_month_data.csv")

    tower_df.to_csv(filename, index=False)
    print(f"[CSV] Saved: {filename}")

print("[OK] 5-Tower MONTH Simulation Completed")

# ---------- VISUALIZE ANIMATION ----------
try:
    animate_monthly_simulation(df, layout)
except Exception as exc:
    print(f"Animation failed: {exc}")
    print("The CSV files were generated successfully.")
