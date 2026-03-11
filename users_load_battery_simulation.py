import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ----------------------------
# PARAMETERS
# ----------------------------
AREA_SIZE = 100
NUM_TOWERS = 12
NUM_USERS = 25
COVERAGE_RADIUS = 28

SIM_TIME = 40
FPS = 5

CAPACITY = 15
P_BASE = 1.2
ALPHA = 0.6
BATTERY_DECAY = 0.08

np.random.seed(7)

# ----------------------------
# IRREGULAR TOWER PLACEMENT
# ----------------------------
tower_positions = np.random.uniform(10, 90, (NUM_TOWERS, 2))
tower_active = [True] * NUM_TOWERS

battery = list(np.random.uniform(80, 100, NUM_TOWERS))
power_levels = [0]*NUM_TOWERS

# ----------------------------
# STATIC USERS (clustered)
# ----------------------------
users = np.vstack([
    np.random.normal([30, 30], 8, (8, 2)),
    np.random.normal([70, 30], 8, (8, 2)),
    np.random.normal([50, 75], 8, (9, 2))
])

users = np.clip(users, 0, AREA_SIZE)
user_demand = np.random.uniform(1, 4, NUM_USERS)

# ----------------------------
# CONNECTION FUNCTION
# ----------------------------
def connect_user(user):
    best = None
    min_dist = 1e9

    for i in range(NUM_TOWERS):
        if not tower_active[i]:
            continue

        dist = np.linalg.norm(user - tower_positions[i])
        if dist <= COVERAGE_RADIUS and dist < min_dist:
            min_dist = dist
            best = i

    return best

# ----------------------------
# FIGURE SETUP
# ----------------------------
fig = plt.figure(figsize=(16, 9))
gs = fig.add_gridspec(2, 3)

ax_map = fig.add_subplot(gs[:, 0])
ax_load = fig.add_subplot(gs[0, 1])
ax_power = fig.add_subplot(gs[0, 2])
ax_battery = fig.add_subplot(gs[1, 1:3])

load_bars = ax_load.bar(range(NUM_TOWERS), [0]*NUM_TOWERS, color='skyblue')
power_bars = ax_power.bar(range(NUM_TOWERS), [0]*NUM_TOWERS, color='orange')
battery_bars = ax_battery.bar(range(NUM_TOWERS), battery, color='lightgreen')

ax_load.set_ylim(0, CAPACITY + 10)
ax_load.set_title("Tower Load")

ax_power.set_ylim(0, 15)
ax_power.set_title("Power Consumption")

ax_battery.set_ylim(0, 100)
ax_battery.set_title("Remaining Battery (%)")

# ----------------------------
# ANIMATION UPDATE
# ----------------------------
def update(frame):

    current_time = frame / FPS
    ax_map.clear()

    tower_load = [0]*NUM_TOWERS

    # Assign users
    for i, user in enumerate(users):
        t = connect_user(user)
        if t is not None:
            tower_load[t] += user_demand[i]

    # Compute power and battery
    for i in range(NUM_TOWERS):

        if tower_active[i]:

            power = P_BASE + ALPHA * tower_load[i]
            power_levels[i] = power

            battery[i] -= BATTERY_DECAY * power

            if battery[i] <= 0:
                battery[i] = 0
                tower_active[i] = False
                power_levels[i] = 0

        else:
            power_levels[i] = 0

    # -------- MAP --------
    ax_map.set_xlim(0, AREA_SIZE)
    ax_map.set_ylim(0, AREA_SIZE)
    ax_map.set_title(f"Time = {current_time:.1f}s")

    for i in range(NUM_TOWERS):
        if tower_active[i]:
            circle = plt.Circle(tower_positions[i],
                                COVERAGE_RADIUS,
                                color='lightblue',
                                alpha=0.15)
            ax_map.add_patch(circle)

    for i in range(NUM_TOWERS):
        color = 'blue' if tower_active[i] else 'gray'
        ax_map.scatter(*tower_positions[i],
                       marker='^',
                       s=150,
                       color=color)

    user_colors = []
    for user in users:
        t = connect_user(user)
        if t is None:
            user_colors.append('red')
        else:
            user_colors.append(f"C{t%10}")

    ax_map.scatter(users[:, 0], users[:, 1],
                   c=user_colors,
                   s=50,
                   edgecolors='black')

    # -------- LOAD BARS --------
    for i in range(NUM_TOWERS):
        load_bars[i].set_height(tower_load[i])

        if not tower_active[i]:
            load_bars[i].set_color('gray')
        elif tower_load[i] > CAPACITY:
            load_bars[i].set_color('red')
        else:
            load_bars[i].set_color('skyblue')

    # -------- POWER BARS --------
    for i in range(NUM_TOWERS):
        power_bars[i].set_height(power_levels[i])

        if not tower_active[i]:
            power_bars[i].set_color('gray')
        else:
            power_bars[i].set_color('orange')

    # -------- BATTERY BARS --------
    for i in range(NUM_TOWERS):
        battery_bars[i].set_height(battery[i])

        if battery[i] <= 0:
            battery_bars[i].set_color('gray')
        elif battery[i] < 30:
            battery_bars[i].set_color('red')
        else:
            battery_bars[i].set_color('lightgreen')

# ----------------------------
# RUN
# ----------------------------
frames = SIM_TIME * FPS
ani = FuncAnimation(fig, update,
                    frames=frames,
                    interval=1000/FPS,
                    repeat=False)

plt.show()