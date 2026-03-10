import simpy
import matplotlib.pyplot as plt
import math
import random

# ==============================
# MINE + ENERGY CONFIGURATION
# ==============================
MINE_WIDTH = 120
MINE_HEIGHT = 80

BATTERY_CAPACITY = 120.0  # Wh (portable mine repeater battery)

MOVE_POWER = 4.0          # W (mobility system)
IDLE_POWER = 3.0          # W (electronics baseline)

P0 = 5.0                  # reference TX power
PMAX = 50.0               # max amplifier power
D0 = 10.0                 # reference distance
PATH_LOSS = 3             # underground attenuation exponent

TRUCK_LOAD_POWER = 6.0    # energy cost per effective truck load
NUM_TRUCKS = 6

SPEED_TOWER = 0.7
SPEED_TRUCK = 1.2

DT = 1
TIME_SCALE = 60           # 1 sec = 1 simulated minute
REALTIME_PAUSE = 0.03

# RF coverage radius derived from power limit
COMM_RADIUS = D0 * (PMAX / P0) ** (1 / PATH_LOSS)

# ==============================
# HELPER FUNCTIONS
# ==============================
def distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def tx_power(d):
    """Distance-based RF transmission cost"""
    if d <= COMM_RADIUS:
        return P0 * (d/D0)**PATH_LOSS
    else:
        return PMAX

def smooth_truck_load(tower_pos, towers, trucks, alpha=2):
    """
    Soft association model:
    each truck contributes gradually to nearby towers.
    """
    load = 0.0
    for truck in trucks:
        weights = []
        for t in towers:
            d = max(distance(truck.pos, t), 1.0)
            weights.append(1/(d**alpha))

        total = sum(weights)
        for t,w in zip(towers,weights):
            if t is tower_pos:
                load += w/total

    return load

# ==============================
# TRUCK MODEL
# ==============================
class Truck:
    def __init__(self, env):
        self.pos = [random.uniform(0,MINE_WIDTH),
                    random.uniform(0,MINE_HEIGHT)]
        self.dx = random.choice([-1,1])
        self.dy = random.choice([-1,1])
        env.process(self.move(env))

    def move(self, env):
        while True:
            self.pos[0] += self.dx * SPEED_TRUCK
            self.pos[1] += self.dy * SPEED_TRUCK

            if self.pos[0] <= 0 or self.pos[0] >= MINE_WIDTH:
                self.dx *= -1
            if self.pos[1] <= 0 or self.pos[1] >= MINE_HEIGHT:
                self.dy *= -1

            yield env.timeout(DT)

# ==============================
# TOWER MODEL (SMOOTH ENERGY)
# ==============================
def moving_tower(env, pos, get_all_towers, get_trucks,
                 pos_log, battery_log):

    battery = BATTERY_CAPACITY
    dx, dy = random.choice([-1,1]), random.choice([-1,1])

    smoothed_power = 0.0
    RAMP = 0.15   # power amplifier inertia (smooth transitions)

    while battery > 0:

        # ---- Move tower ----
        pos[0] += dx * SPEED_TOWER
        pos[1] += dy * SPEED_TOWER

        if pos[0] <= 0 or pos[0] >= MINE_WIDTH:
            dx *= -1
        if pos[1] <= 0 or pos[1] >= MINE_HEIGHT:
            dy *= -1

        towers = get_all_towers()
        trucks = get_trucks()

        # ---- Mesh communication energy ----
        mesh_power = 0
        for other in towers:
            if other is not pos:
                mesh_power += tx_power(distance(pos, other))

        # ---- Truck load (smooth, no hard switching) ----
        load = smooth_truck_load(pos, towers, trucks)
        truck_power = TRUCK_LOAD_POWER * load

        target_power = MOVE_POWER + IDLE_POWER + mesh_power + truck_power

        # ---- Smooth hardware response ----
        smoothed_power += RAMP * (target_power - smoothed_power)

        # ---- Battery discharge ----
        battery -= smoothed_power * ((DT * TIME_SCALE)/3600)

        pos_log.append((pos[0],pos[1]))
        battery_log.append((env.now,battery))

        yield env.timeout(DT)

# ==============================
# SIMULATION SETUP
# ==============================
env = simpy.Environment()

pos_A = [20,20]
pos_B = [90,40]
pos_C = [60,10]
towers = [pos_A,pos_B,pos_C]

trucks = [Truck(env) for _ in range(NUM_TRUCKS)]

log_A,log_B,log_C = [],[],[]
bat_A,bat_B,bat_C = [],[],[]

env.process(moving_tower(env,pos_A,lambda:towers,lambda:trucks,log_A,bat_A))
env.process(moving_tower(env,pos_B,lambda:towers,lambda:trucks,log_B,bat_B))
env.process(moving_tower(env,pos_C,lambda:towers,lambda:trucks,log_C,bat_C))

# ==============================
# PLOTTING
# ==============================
plt.ion()
fig,axs = plt.subplots(1,4,figsize=(22,5))

axs[0].set_xlim(0,MINE_WIDTH)
axs[0].set_ylim(0,MINE_HEIGHT)
axs[0].set_title("Coal Mine Network with Trucks")
axs[0].grid()

pA,=axs[0].plot([],[],'ro',label="Tower A")
pB,=axs[0].plot([],[],'bo',label="Tower B")
pC,=axs[0].plot([],[],'go',label="Tower C")

truck_plot,=axs[0].plot([],[],'ks',markersize=4,label="Trucks")

# Coverage circles
circleA = plt.Circle((0,0),COMM_RADIUS,color='r',alpha=0.12)
circleB = plt.Circle((0,0),COMM_RADIUS,color='b',alpha=0.12)
circleC = plt.Circle((0,0),COMM_RADIUS,color='g',alpha=0.12)

axs[0].add_patch(circleA)
axs[0].add_patch(circleB)
axs[0].add_patch(circleC)
axs[0].legend()

plots=[]
for ax,title,color in zip(axs[1:],["Battery A","Battery B","Battery C"],['r','b','g']):
    ax.set_title(title)
    ax.set_ylim(0,BATTERY_CAPACITY)
    ax.grid()
    p,=ax.plot([],[],color)
    plots.append(p)

# ==============================
# REAL-TIME LOOP
# ==============================
while True:
    try:
        env.step()

        if log_A:
            x,y=log_A[-1]
            pA.set_data([x],[y])
            circleA.center=(x,y)

        if log_B:
            x,y=log_B[-1]
            pB.set_data([x],[y])
            circleB.center=(x,y)

        if log_C:
            x,y=log_C[-1]
            pC.set_data([x],[y])
            circleC.center=(x,y)

        truck_plot.set_data([t.pos[0] for t in trucks],
                            [t.pos[1] for t in trucks])

        for i,log in enumerate([bat_A,bat_B,bat_C]):
            if log:
                t,b=zip(*log)
                plots[i].set_data(t,b)
                axs[i+1].set_xlim(0,max(t)+5)

        plt.pause(REALTIME_PAUSE)

    except simpy.core.EmptySchedule:
        break

plt.ioff()
plt.show()
