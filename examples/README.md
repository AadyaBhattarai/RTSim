# Examples

Minimal working examples for running RTSim simulations.

## Quick Start

```bash
# Car-following (no Plexe needed)
python examples/example_car_following.py

# Platooning (requires Plexe)
python examples/example_platooning.py
```

Both scripts demonstrate a single-scenario run without parallel processing — the simplest way to verify your setup works.

---

## Folder Structure: PLATOONING vs CAR FOLLOWING

### Platooning Route Templates

```
{route_base_dir}/                        ← Platooning route templates
├── Model1/
│   ├── 1truck/
│   │   └── 90/                          ← Speed label
│   │       ├── lower/
│   │       │   └── grade01.rou.xml      ← Route file
│   │       └── upper/
│   │
│   ├── 2truck/
│   │   └── 90/
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

### Car-Following Route Templates

```
{route_base_dir}/                        ← Car-following route templates
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

| Aspect | Platooning | Car-Following |
|--------|------------|---------------|
| Route file name | `grade01.rou.xml` | `grade2.rou.xml` |
| Has speed subfolder | Yes (`/90/`) | No |
| Has gap subfolder | Yes for 2+ trucks (`/5/`) | No |
| Parameters in XML | Fixed (Cd set via PHEMlight) | Modified via regex (σ, τ, speed) |

---

## PHEMlight Folder Structure

```
PHEMlight/
├── Model1/
│   ├── 2truck/                          ← PLATOONING (reduced drag)
│   │   └── 5/
│   │       └── 90/
│   │           ├── Lower/
│   │           │   ├── RT_II_D_EU0.veh  ← Lead vehicle Cd
│   │           │   └── RT_II_D_EU1.veh  ← Follower Cd
│   │           └── Upper/
│   │
│   └── Single/                          ← CAR-FOLLOWING (normal drag)
│       └── 90/
│           ├── Lower/
│           │   └── RT_II_D_EU0.veh
│           └── Upper/
```

---

## How Position Maps to PHEMlight Files

Each vehicle ID in the platoon is assigned a different vType, which points to a position-specific PHEMlight emission file:

```
v.0.0 → vtypeauto1 → emissionClass="PHEMlight/.../RT_II_D_EU0"  (lead Cd)
v.0.1 → vtypeauto2 → emissionClass="PHEMlight/.../RT_II_D_EU1"  (follower Cd)
v.0.2 → vtypeauto3 → emissionClass="PHEMlight/.../RT_II_D_EU2"  (trailing Cd)
```

This mapping is handled by `src/platooning/plexe_utils.py`.

---

## Why Lower and Upper?

Since exact drag values are uncertain, simulations run with both:
- **Lower**: Lower bound Cd estimate → lower fuel consumption
- **Upper**: Upper bound Cd estimate → higher fuel consumption

Results from both are averaged to produce final estimates with confidence intervals.

---

## Route File → PHEMlight Connection

### Platooning Route File
```xml
<vType id="vtypeauto1"
       emissionClass="PHEMlight/Model1/2truck/5/90/Lower/RT_II_D_EU0"/>
<vType id="vtypeauto2"
       emissionClass="PHEMlight/Model1/2truck/5/90/Lower/RT_II_D_EU1"/>
```

### Car-Following Route File
```xml
<vType id="DAC_army"
       emissionClass="PHEMlight/Model1/Single/90/Lower/RT_II_D_EU0"/>
```

---

## Example Code Usage

### Platooning

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core import SimulationBase, NetworkGenerator, RouteGenerator
from src.platooning import run_platooning_simulation
from src.utils import CRRModifier

# Generate networks
net_gen = NetworkGenerator("output/networks")
networks = net_gen.generate_networks("experiment.xodr", "network", [0.0, 0.04])

# Generate routes
route_gen = RouteGenerator("route_templates/", "output/routes")
routes = route_gen.generate_platooning_routes(...)

# Modify CRR (platooning uses .veh suffix)
crr_mod = CRRModifier("/path/to/emissions", ".veh")
crr_mod.modify_crr_for_routes(routes, "primary")

# Run
cfg = SimulationBase.generate_config("grade0.sumocfg", routes[0], networks[0][1])
results = run_platooning_simulation(cfg, routes[0], speed=90)
```

### Car-Following

```python
from src.core import SimulationBase, NetworkGenerator, RouteGenerator
from src.car_following import run_car_following_simulation
from src.utils import CRRModifier

# Generate routes
route_gen = RouteGenerator("route_templates/", "output/routes")
routes = route_gen.generate_car_following_routes(...)

# Modify CRR (car-following uses .PHEMLight.veh suffix)
crr_mod = CRRModifier("/path/to/emissions", ".PHEMLight.veh")
crr_mod.modify_crr_for_routes(routes, "cross_country")

# Run (seed for randomization, no Plexe needed)
cfg = SimulationBase.generate_config("grade0.sumocfg", routes[0], networks[0][1])
results = run_car_following_simulation(cfg, routes[0], seed=42)
```

---

## Included Example Files

| File | Description |
|------|-------------|
| `example_platooning.py` | Minimal single-scenario platooning run |
| `example_car_following.py` | Minimal single-scenario car-following run |
| `simulation/` | Example platooning route templates and PHEMlight files for Model1 |
| `car-following/` | Example car-following route template for Model1 |
