# Test Simulation Mathematical Model Documentation

## Overview

The Test simulation models a realistic 5-tower mine communication network with 30-day temporal dynamics. The simulation captures tower power consumption, battery state-of-charge (SOC), user demand, coverage dynamics, and environmental factors to provide realistic operational insights for mine telecommunications systems.

**Simulation Parameters:**
- Duration: 30 days
- Time step: 5 minutes
- Number of towers: 15 (dynamically repositioned daily)
- Grid size: 1000m × 1000m
- Season: Summer

---

## 1. Temperature Model

### Mathematical Formulation

Temperature is modeled as a sinusoidal daily cycle with seasonal mean and amplitude, plus random noise:

$$T(h) = T_{\text{mean}} + A \sin\left(\frac{2\pi(h - 6)}{24}\right) + \epsilon$$

Where:
- $T(h)$ = Temperature at hour $h$ (°C)
- $T_{\text{mean}}$ = Seasonal mean temperature
- $A$ = Daily amplitude (oscillation range)
- $h$ = Hour of day (0-23)
- $\epsilon$ = Random noise: $\epsilon \sim \mathcal{N}(0, 0.5)$

### Seasonal Parameters

| Season | Mean (°C) | Amplitude (°C) |
|--------|-----------|----------------|
| Summer | 38 | 7 |
| Winter | 20 | 5 |
| Spring/Fall | 30 | 6 |

### Key Characteristics

- **Peak temperature** occurs at hour ~12 (noon)
- **Minimum temperature** occurs at hour ~6 (early morning)
- Temperature variation is realistic for daily environmental cycles
- Gaussian noise adds realistic measurement uncertainty



---

## 2. User Demand Model

### Mathematical Formulation

User demand follows a daily pattern with peak demand during working hours:

$$U(h) = U_{\text{max}} \left(0.25 + 0.75 \sin^2\left(\frac{2\pi(h - 8)}{24}\right)\right) + \delta$$

Where:
- $U(h)$ = Number of users at hour $h$
- $U_{\text{max}}$ = Maximum concurrent users (500 in test config)
- $h$ = Hour of day
- $\delta$ = Daily random fluctuation: $\delta \sim \mathcal{N}(0, 15)$

### Model Characteristics

- **Base demand**: 25% of maximum (off-hours)
- **Peak demand**: 100% of maximum (working hours 8:00 - 16:00)
- **Working hours peak**: ~12:00 noon
- **Smooth transitions**: Sinusoidal shape avoids artificial discontinuities
- **Realistic variability**: Gaussian noise simulates unpredictable user behavior (conferences, emergencies, etc.)

### Output Range
- Minimum: ~125 users (25% of 500)
- Maximum: ~500 users
- Average: ~370 users


---

## 3. Coverage Model

### Mathematical Formulation

Effective coverage radius is adjusted by terrain factors:

$$R_{\text{eff}}(t) = R_{\text{base}} \cdot F_{\text{terrain}}(t)$$

Where:
- $R_{\text{eff}}$ = Effective coverage radius (meters)
- $R_{\text{base}}$ = Base coverage radius (250m)
- $F_{\text{terrain}}$ = Terrain adjustment factor (typically 0.8 - 1.2)

### Coverage Load Factor

User density within coverage area affects power requirements:

$$L_{\text{coverage}} = \frac{\text{users}}{\pi R_{\text{eff}}^2} \times 1000$$

Where:
- $L_{\text{coverage}}$ = Coverage load (normalized user density)
- Scaling factor (1000) brings values to practical range

### Noise Application

Realistic measurement variability is added:

$$L_{\text{coverage, reported}} = L_{\text{coverage}} \cdot (1 + \eta)$$

Where:
- $\eta \sim \mathcal{N}(0, 0.05)$ (5% measurement noise)

### Typical Values

- Base radius: 250m
- Coverage area: ~196,350 m² (at base radius)
- Radius range: 200m - 300m (with terrain variation)
- Load range: 0.0 - 40+ (proportional to user density)

---

## 4. Terrain Model

### Mathematical Formulation

Terrain factors introduce realistic spatial variability in signal propagation and coverage:

$$F_{\text{terrain}}(t) = F_{\text{base}} \cdot (1 + \zeta)$$

Where:
- $F_{\text{terrain}}$ = Terrain adjustment factor
- $F_{\text{base}}$ = Base factor (1.0)
- $\zeta$ = Random terrain variation: $\zeta \sim \mathcal{N}(0, 0.18)$

### Model Interpretation

- **Factor > 1.0**: Favorable terrain (open areas, elevated positions)
- **Factor = 1.0**: Neutral baseline
- **Factor < 1.0**: Unfavorable terrain (valleys, obstructions)

### Applications

- **Coverage radius adjustment**: $R_{\text{eff}} = R_{\text{base}} \cdot F_{\text{terrain}}$
- **TX power adjustment**: $P_{\text{TX}} = P_{\text{base}} \cdot F_{\text{terrain}} \cdot (1 + \eta_{\text{power}})$

### Noise Scale
- Standard deviation: 0.18 (18% variability)
- Realistic range: 0.64 - 1.36 (±3σ)


---

## 5. Battery Model

### 5.1 Power Consumption

Total power consumption combines multiple sources:

$$P_{\text{total}}(t) = P_{\text{idle}} + 0.35 \cdot U_{\text{eff}} + 0.0009 \cdot P_{\text{TX}}^2 + 2 \cdot L_{\text{coverage}} + 0.03 \cdot e^{T/40}$$

Where:
- $P_{\text{idle}}$ = Idle/baseline power (60W)
- $U_{\text{eff}}$ = Effective users assigned to tower
- $P_{\text{TX}}$ = Transmit power (W)
- $L_{\text{coverage}}$ = Coverage load metric
- $T$ = Ambient temperature (°C)

#### Power Component Breakdown

| Component | Coefficient | Description |
|-----------|-------------|-------------|
| Idle power | 60 W | Always-on equipment (cooling, monitoring, lighting) |
| User processing | 0.35 W/user | Processing load from active users |
| TX power squared | 0.0009 | Nonlinear power amplifier efficiency losses |
| Coverage load | 2 W per load unit | Signal reception/processing overhead |
| Temperature term | 0.03 × exp(T/40) | Temperature-dependent cooling needs |
| Event spike | 1.0 - 1.36× | Occasional 12-24% power spikes (3.5% probability) |

#### Temperature Sensitivity

The exponential temperature term models increased cooling requirements:

$$P_{\text{cooling}} = 0.03 \cdot e^{T/40}$$

- At T = 20°C: ~0.045 W additional power
- At T = 38°C: ~0.048 W additional power
- At T = 50°C: ~0.052 W additional power

### 5.2 Battery State of Charge Update

SOC evolution over time step $\Delta t$ (hours):

$$\text{SOC}_{t+1} = \text{SOC}_t - \frac{P_{\text{total}} \cdot \Delta t \cdot \eta}{C_{\text{capacity}}} \times 100$$

Where:
- $\eta$ = Battery efficiency/inefficiency factor: $\eta \sim \mathcal{N}(0.95, 0.05)$ (clipped to [0.85, 1.0])
- $C_{\text{capacity}}$ = Current battery capacity (Wh)
- Factor of 100 converts to percentage

### 5.3 Battery Degradation

Capacity decreases over time to simulate battery aging:

$$C_{\text{capacity}, t+1} = C_{\text{capacity}, t} \cdot \left(1 - \lambda \cdot \frac{\Delta t}{24}\right)$$

Where:
- $\lambda$ = Degradation rate: $\lambda \sim \mathcal{U}(0.0003, 0.0007)$ per day
- Capacity is bounded: $C_{\text{capacity}} \geq 0.8 \cdot C_{\text{initial}}$

**Interpretation:**
- ~0.03% to 0.07% capacity loss per day
- Prevents unrealistic infinite battery performance
- After 30 days: ~1% to 2% total capacity loss

### 5.4 Battery Recharge Logic

Realistic recharge behavior when SOC reaches 0%:

1. When $\text{SOC} = 0$, increment recharge timer: $t_{\text{recharge}} += \Delta t$
2. If $t_{\text{recharge}} \geq t_{\text{recharge, limit}}$:
   - Reset SOC to random value: $\text{SOC} \sim \mathcal{U}(80, 100)$ %
   - Reset timer and generate new recharge interval: $t_{\text{limit}} \sim \mathcal{U}(2, 10)$ hours

### 5.5 SOC Measurement Noise

Reported SOC includes sensor noise:

$$\text{SOC}_{\text{reported}} = \text{SOC}_{\text{actual}} + \xi$$

Where:
- $\xi \sim \mathcal{N}(0, 0.9)$ (0.9% standard deviation)
- Clipped to valid range: $[0, 100]$ %

### Initial Conditions

| Parameter | Value | Notes |
|-----------|-------|-------|
| Battery capacity | 5000 Wh | ~5 kWh per tower |
| Initial SOC | 100% | All towers fully charged at start |
| Idle power | 60 W | Conservative baseline |
| Measurement noise | 0.9% | ~1% uncertainty |


---

## 6. Load Sharing Model

### Mathematical Formulation

Users are redistributed across towers based on available battery capacity:

$$U_{\text{eff}, i} = \frac{\text{SOC}_i}{\sum_j \text{SOC}_j} \times U_{\text{total}}$$

Where:
- $U_{\text{eff}, i}$ = Effective users assigned to tower $i$
- $\text{SOC}_i$ = State of charge of tower $i$ battery (%)
- $U_{\text{total}}$ = Total users in coverage area

### Model Rationale

- **Healthier batteries attract more load**: Higher SOC towers take more users
- **Prevents tower blackout**: Failed towers naturally receive fewer users
- **Automatic load balancing**: No complex routing logic needed
- **Realistic failure modes**: Low-SOC towers gracefully degrade

### Numerical Stability

To prevent division by zero:

$$U_{\text{eff}, i} = \frac{\text{SOC}_i}{\sum_j \text{SOC}_j + 10^{-6}} \times U_{\text{total}}$$


---

## 7. Tower Positioning & User Assignment

### User Position Sampling

Users are sampled along operational routes or uniformly:

1. **Route-based positioning** (if route available):
   - Sample from predefined MAP route points
   - Add Gaussian jitter: $\mathcal{N}(0, 15)$ m

2. **Fallback uniform sampling**:
   - $\text{User position} \sim \mathcal{U}([0, 1000] \times [0, 1000])$ m

### Tower Assignment

Users assigned to nearest tower within coverage radius:

$$\text{Assign user to tower } i \text{ if:} \quad d_i = \min_j \{d_j : d_j \leq R_{j,\text{eff}}\}$$

Where:
- $d_i$ = Euclidean distance to tower $i$
- $R_{j,\text{eff}}$ = Effective coverage radius of tower $j$

### Daily Tower Repositioning

Towers are repositioned daily using k-means clustering:

1. **Sample user positions** at 3 times: 6:00, 12:00, 18:00
2. **Cluster** into k=15 groups (number of towers)
3. **Move towers** to cluster centroids
4. **Update** 3D positions using terrain surface projection

---

## 8. Output Parameters

### Recorded Metrics (Every 5 minutes)

| Parameter | Unit | Description | Source |
|-----------|------|-------------|--------|
| `datetime` | timestamp | Simulation time (YYYY-MM-DD HH:MM:SS) | Simulator |
| `tower_id` | index | Tower identifier (0-14) | Configuration |
| `x_m` | meter | Tower X position | Layout |
| `y_m` | meter | Tower Y position | Layout |
| `z_m` | meter | Tower Z position (elevation) | Terrain surface projection |
| `temperature_degC` | °C | Ambient temperature | TemperatureModel |
| `effective_users` | count | Users assigned to tower | LoadSharingModel |
| `coverage_radius_m` | meter | Effective coverage radius | CoverageModel |
| `coverage_load` | normalized | User density metric | CoverageModel.load_factor() |
| `tx_power_W` | watts | Transmit power | Terrain × Base power |
| `power_consumption_W` | watts | Total power draw | BatteryModel.compute_power() |
| `battery_soc_percent` | % | Battery state of charge | BatteryModel.update() |

### Data Aggregation

Output is saved as:
- **Per-tower CSV files**: `tower_{id}_month_data.csv`
- **Individual records**: One row per 5-minute time step per tower
- **Total records**: ~432,000 (30 days × 24 hours × 12 steps × 15 towers)

---

## 9. Noise and Uncertainty

### Applied Noise Levels

| Model Component | Noise Type | Magnitude | Rationale |
|-----------------|-----------|-----------|-----------|
| Battery parameters | Gaussian | 8% | Manufacturing variability |
| Coverage radius | Gaussian | 6% | Terrain/fading uncertainty |
| TX power | Gaussian | 8% | Power supply variation |
| User demand | Gaussian | ±15 users | Daily fluctuations |
| Terrain factor | Gaussian | 18% | Spatial propagation variation |
| Coverage load | Gaussian | 5% | Measurement uncertainty |
| Temperature | Gaussian | ±0.5°C | Sensor noise |
| SOC measurement | Gaussian | ±0.9% | Battery monitor uncertainty |
| Event spike | Uniform | 12-24% | Occasional power surges (3.5% prob) |

### Noise Purposes

- **Prevents artificial periodicity** in output
- **Simulates real measurement uncertainties**
- **Captures environmental stochasticity**
- **Enables ensemble studies** for uncertainty quantification

---

## 10. Key Assumptions & Limitations

### Assumptions

1. **Linear user demand processing**: Power ∝ users (ignores protocol overhead)
2. **Ideal tower coverage**: Binary assignment (inside/outside radius)
3. **No inter-tower communication**: Each tower independent for coverage/power
4. **Ideal load sharing**: Proportional to SOC, no transport delays
5. **No weather events**: Temperature follows smooth sine curve
6. **Constant user location**: No time-dependent mobility patterns
7. **Tower repositioning**: Instantaneous daily updates

### Limitations

1. **Simplified power model**: Quadratic TX power loss is approximate
2. **No fading/path loss**: Coverage radius is fixed
3. **No interference**: Towers don't interfere with each other
4. **No maintenance events**: No unplanned downtime
5. **Terrain effects**: Only affects coverage, not propagation delay
6. **No traffic routing**: All users can freely access any tower
7. **Daily repositioning**: Assumes perfect placement knowledge

---

## 11. Validation Ranges

### Sanity Checks for Output

| Parameter | Min | Typical | Max | Unit |
|-----------|-----|---------|-----|------|
| Temperature | 15 | 33 | 50 | °C |
| Effective users | 0 | 180 | 450 | count |
| Coverage radius | 200 | 250 | 300 | m |
| Coverage load | 0 | 15 | 40+ | normalized |
| TX power | 80 | 120 | 180 | W |
| Power consumption | 100 | 200 | 400+ | W |
| Battery SOC | 0 | 65 | 100 | % |

---

## 12. Mathematical Symbols Reference

| Symbol | Definition |
|--------|-----------|
| $T(h)$ | Temperature at hour $h$ |
| $U(h)$ | User count at hour $h$ |
| $R_{\text{eff}}$ | Effective coverage radius |
| $F_{\text{terrain}}$ | Terrain adjustment factor |
| $L_{\text{coverage}}$ | Coverage load metric |
| $P_{\text{total}}$ | Total power consumption |
| $P_{\text{TX}}$ | Transmit power |
| $\text{SOC}$ | Battery state of charge (%) |
| $C_{\text{capacity}}$ | Battery capacity (Wh) |
| $\lambda$ | Battery degradation rate |
| $\eta$ | Battery efficiency factor |
| $\epsilon, \delta, \zeta, \xi, \eta_{\text{power}}$ | Various noise terms |
| $\mathcal{N}(\mu, \sigma)$ | Normal distribution, mean $\mu$, std dev $\sigma$ |
| $\mathcal{U}(a, b)$ | Uniform distribution on $[a, b]$ |

---

## 13. References & Further Reading

- **Signal propagation**: Coverage radius models simplified path loss
- **Battery modeling**: Based on standard lithium-ion discharge curves
- **Load balancing**: Proportional-to-capacity approach (common in cloud systems)
- **User demand**: Daily sine pattern reflects typical telecom traffic
- **Terrain effects**: Random factors approximate real spatial variability

---

*Document Generated: April 2026*
*Simulation System: MineInsite*
