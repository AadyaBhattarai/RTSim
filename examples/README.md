# Examples

This folder contains example files and scripts for running simulations.

## Example Scripts

```bash
# Platooning simulation
python examples/example_platooning.py

# Car following simulation
python examples/example_car_following.py
```

---

## Folder Structure: PLATOONING vs CAR FOLLOWING

### Platooning Route Templates

```
simulation/                              ← Platooning route templates
├── Model1/
│   ├── 1truck/
│   │   └── 90/                          ← Speed
│   │       ├── lower/
│   │       │   └── grade01.rou.xml      ← Route file
│   │       └── upper/
│   │
│   ├── 2truck/
│   │   └── 90/                          ← Speed
│   │       ├── 5/                       ← Gap (meters)
│   │       │   ├── lower/
│   │       │   │   └── grade01.rou.xml
│   │       │   └── upper/
│   │       ├── 10/
│   │       ├── 15/
│   │       └── 20/
│   │
│   └── 3truck/
│       └── ...
```

### Car Following Route Templates

```
carfollowing/                            ← Car following route templates
├── Model1/
│   ├── 1truck/
│   │   ├── lower/
│   │   │   └── grade2.rou.xml           ← Route file (different name!)
│   │   └── upper/
│   │
│   └── 2truck/
│       ├── lower/
│       │   └── grade2.rou.xml
│       └── upper/
```

**Key Differences:**
| Aspect | Platooning | Car Following |
|--------|------------|---------------|
| Route file name | `grade01.rou.xml` | `grade2.rou.xml` |
| Has speed subfolder | Yes (`/90/`) | No |
| Has gap subfolder | Yes for 2+ trucks (`/5/`) | No |

---

## PHEMlight Folder Structure

```
PHEMlight/
├── Model1/
│   ├── 2truck/                          ← PLATOONING (reduced drag)
│   │   └── 5/
│   │       └── 90/
│   │           ├── Lower/
│   │           │   └── RT_II_D_EU0.veh
│   │           └── Upper/
│   │
│   └── Single/                          ← CAR FOLLOWING (normal drag)
│       └── 90/
│           ├── Lower/
│           │   └── RT_II_D_EU0.veh
│           └── Upper/
```

---

## Why Different Drag Coefficients?

### Platooning (2truck, 3truck, etc.)
- Vehicles travel close together in a platoon
- Following vehicles benefit from **reduced air drag** (slipstreaming effect)
- Lower CdA (drag coefficient) in PHEMlight files
- Example: `CdA = 0.45` (reduced)

### Car Following (Single)
- Vehicles operate independently
- **No drag reduction** benefit
- Normal CdA in PHEMlight files
- Example: `CdA = 0.65` (normal)

---

## Route File → PHEMlight Connection

### Platooning Route File
```xml
<vType id="vtypeauto1" 
       emissionClass="PHEMlight/Model1/2truck/5/90/Lower/RT_II_D_EU0"/>
```
Points to: `PHEMlight/Model1/2truck/5/90/Lower/RT_II_D_EU0.veh`

### Car Following Route File
```xml
<vType id="DAC_army" 
       emissionClass="PHEMlight/Model1/Single/90/Lower/RT_II_D_EU0"/>
```
Points to: `PHEMlight/Model1/Single/90/Lower/RT_II_D_EU0.veh`

---

## Why Lower and Upper?

Since exact drag values are unknown, simulations run with both:
- **Lower**: Lower bound drag estimate → lower fuel consumption
- **Upper**: Upper bound drag estimate → higher fuel consumption

This gives a range of results.

---

## Example Code Usage

### Platooning

```python
from core import SimulationBase, NetworkGenerator, RouteGenerator
from platooning import run_platooning_simulation
from utils import CRRModifier

# Generate networks
net_gen = NetworkGenerator("output/networks")
networks = net_gen.generate_networks("experiment.xodr", "network", [0.0, 0.04])

# Generate routes (uses simulation/ folder structure)
route_gen = RouteGenerator("simulation/", "output/routes")
routes = route_gen.generate_platooning_routes(...)

# Modify CRR (.veh suffix for platooning)
crr_modifier = CRRModifier("PHEMlight/", ".veh")
crr_modifier.modify_crr_for_routes(routes, "primary", crr_values)

# Run
results = run_platooning_simulation(cfg, route, speed=90)
```

### Car Following

```python
from core import SimulationBase, NetworkGenerator, RouteGenerator
from car_following import run_car_following_simulation
from utils import CRRModifier

# Generate routes (uses carfollowing/ folder structure)
route_gen = RouteGenerator("carfollowing/", "output/routes")
routes = route_gen.generate_car_following_routes(...)

# Modify CRR (.PHEMLight.veh suffix for car following)
crr_modifier = CRRModifier("PHEMlight/", ".PHEMLight.veh")
crr_modifier.modify_crr_for_routes(routes, "cross_country", crr_values)

# Run (seed for randomization, no Plexe needed)
results = run_car_following_simulation(cfg, route, seed=42)
```
