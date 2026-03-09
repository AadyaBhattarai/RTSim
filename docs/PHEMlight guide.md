# PHEMlight Emission Files in RTSim

## Overview

RTSim uses the **PHEMlight emission model** (instead of SUMO's default HBEFA model) to calculate fuel consumption. PHEMlight computes fuel consumption from first principles using the equation:

```
P_e = (P_roll + P_air + P_grad + P_accel) / η_gearbox
```

Where:
- `P_roll` = rolling resistance power (depends on mass, road roughness)
- `P_air` = aerodynamic drag power (**depends on Cd and frontal area**)
- `P_grad` = gradient power (depends on road grade)
- `P_accel` = acceleration power
- `η_gearbox` = gearbox efficiency

The key advantage of PHEMlight over HBEFA is that it **explicitly models each force component**, allowing us to modify the drag coefficient (Cd) for each vehicle in a platoon based on its position.

## Why Each Vehicle Needs Its Own Emission File

In a platoon, vehicles experience different aerodynamic forces depending on their position:

```
Wind →   [Vehicle 1]  gap  [Vehicle 2]  gap  [Vehicle 3]
           (lead)            (middle)           (trailing)
         
         Higher Cd         Lower Cd           Lowest Cd
         (faces full       (reduced front     (sheltered by
          airflow)          pressure)           two vehicles)
```

The lead vehicle faces full aerodynamic drag but benefits from reduced back-pressure caused by the following vehicle. Middle and trailing vehicles operate in the low-velocity wake of preceding vehicles, significantly reducing their drag.

**These drag reductions are not linear** — they depend on:
- Vehicle shape (bluff body geometry)
- Inter-vehicle gap (5m, 10m, 15m, 20m)
- Number of vehicles in the platoon
- Speed (higher speeds amplify aerodynamic effects)

We determined the Cd values for each configuration using **Computational Fluid Dynamics (CFD)** simulations in OpenFOAM (see Section 4 of the paper).

## The .veh File Format

Each `.veh` file is a text file that defines a vehicle's powertrain characteristics. Here are the key fields that RTSim modifies:

```
c Vehicle mass [kg]
9507.0                          ← Vehicle mass
c Vehicle loading [kg]
10000.0                         ← Cargo weight
c Cd value [-]
0.636723                        ← DRAG COEFFICIENT (changes per position/gap)
c Cross sectional area [m^2]
5.92                            ← Frontal area
...
c Rolling resistance coefficients
c Fr0
0.006923                        ← ROLLING RESISTANCE (changes per road type)
c Fr1
0
...
c Engine rated power [kW]
205                             ← Engine power
...
```

**Two fields change at runtime:**
1. **Cd value** — Set during file generation based on CFD results for position/gap
2. **Fr0** — Modified before each simulation based on road type (primary/secondary/cross-country)

## Folder Structure

```
PHEMlight/
├── {Model}/
│   ├── Single/                          ← Car-following (no drag reduction)
│   │   └── 90/                          ← Speed label
│   │       ├── Lower/                   ← Lower bound of Cd range
│   │       │   ├── RT_II_D_EU0.veh     ← Vehicle file
│   │       │   ├── RT_II_D_EU0.csv     ← Emission curves
│   │       │   └── RT_II_D_EU0_FC.csv  ← Fuel consumption curves
│   │       └── Upper/                   ← Upper bound of Cd range
│   │           └── ...
│   │
│   ├── 2truck/                          ← 2-vehicle platoon
│   │   ├── 5/                           ← 5-meter gap
│   │   │   └── 90/
│   │   │       ├── Lower/
│   │   │       │   ├── RT_II_D_EU0.veh  ← Lead vehicle (position 1)
│   │   │       │   └── RT_II_D_EU1.veh  ← Follower (position 2)
│   │   │       └── Upper/
│   │   │           ├── RT_II_D_EU0.veh
│   │   │           └── RT_II_D_EU1.veh
│   │   ├── 10/                          ← 10-meter gap
│   │   ├── 15/
│   │   └── 20/
│   │
│   └── 3truck/                          ← 3-vehicle platoon
│       ├── 5/
│       │   └── 90/
│       │       ├── Lower/
│       │       │   ├── RT_II_D_EU0.veh  ← Lead (position 1)
│       │       │   ├── RT_II_D_EU1.veh  ← Middle (position 2)
│       │       │   └── RT_II_D_EU2.veh  ← Trailing (position 3)
│       │       └── Upper/
│       ├── 10/
│       ├── 15/
│       └── 20/
```

### Naming Convention

| File | Position | Description |
|------|----------|-------------|
| `RT_II_D_EU0.veh` | 1 (lead) | Faces full airflow, some back-pressure benefit |
| `RT_II_D_EU1.veh` | 2 (middle/follower) | Reduced front pressure from lead's wake |
| `RT_II_D_EU2.veh` | 3 (trailing) | Most sheltered, lowest Cd |

### Why Lower and Upper?

The base Cd for each vehicle model is provided as a **range** (e.g., 0.7–0.95 for M1078). The CFD analysis gives a **percentage reduction** for each platoon position. We apply this reduction to both bounds:

```
Example: M1078 (Model1), 2-truck platoon, 5m gap, position 1 (lead)
  Base Cd range:     0.70 – 0.95
  CFD reduction:     ~9.0%
  Lower bound Cd:    0.70 × (1 - 0.090) = 0.637  → RT_II_D_EU0.veh in Lower/
  Upper bound Cd:    0.95 × (1 - 0.090) = 0.864  → RT_II_D_EU0.veh in Upper/
```

Running with both bounds gives a **range of fuel consumption estimates**, from which we report means and confidence intervals.

## How Route Files Reference PHEMlight Files

Each vehicle type in the SUMO route file (`.rou.xml`) specifies its emission file via the `emissionClass` attribute:

```xml
<!-- 3-truck platoon, Model4, 5m gap, Lower bound -->
<vType id="vtypeauto1" ... emissionClass="PHEMlight/Model4/3truck/5/90/Lower/RT_II_D_EU0"/>
<vType id="vtypeauto2" ... emissionClass="PHEMlight/Model4/3truck/5/90/Lower/RT_II_D_EU1"/>
<vType id="vtypeauto3" ... emissionClass="PHEMlight/Model4/3truck/5/90/Lower/RT_II_D_EU2"/>
```

SUMO resolves this path relative to its emission data directory (`$SUMO_HOME/data/emissions/`).

## Companion Files (.csv and _FC.csv)

Each `.veh` file has two companion CSV files:

| File | Contents |
|------|----------|
| `RT_II_D_EU0.csv` | Emission curves (NOx, HC, CO, PM, etc.) as function of normalized power |
| `RT_II_D_EU0_FC.csv` | Fuel consumption curve as function of normalized power |

These files define how emissions and fuel consumption vary with engine load. They are **the same for all positions and gaps** within a model — only the `.veh` file changes (because only Cd changes).

## Generating PHEMlight Files

Use the provided tool to auto-generate the complete folder tree:

```bash
python tools/generate_phemlight_files.py \
    --base-veh data/base_phemlight/Model1_base.veh \
    --cd-csv data/drag_coefficients.csv \
    --output-dir PHEMlight \
    --model Model1
```

To generate for all models at once:

```bash
python tools/generate_phemlight_files.py \
    --base-veh-dir data/base_phemlight/ \
    --cd-csv data/drag_coefficients.csv \
    --output-dir PHEMlight
```

## Using Your Own Vehicles

To use RTSim with your own vehicles:

1. Obtain a base PHEMlight `.veh` file for your vehicle type from [TU Graz](https://www.tugraz.at/) or create one with the correct powertrain parameters.
2. Run CFD simulations for your vehicle geometry to determine Cd reductions for different platoon configurations. We used OpenFOAM with k-ω SST turbulence model.
3. Create a `drag_coefficients.csv` with your Cd values following the format in `data/drag_coefficients.csv`.
4. Run `generate_phemlight_files.py` to create the folder tree.
5. Create corresponding route file templates with matching `emissionClass` paths.

## Rolling Resistance Modification

Before running a simulation, RTSim modifies the Fr0 value in the `.veh` files based on the road type:

| Road Type | Fr0 Value | Source |
|-----------|-----------|--------|
| Primary (highways) | 0.006923 | PHEMlight default for heavy-duty vehicles |
| Secondary (arterial) | 0.010 | Estimated from Handbook (2011); Chen et al. (2016) |
| Cross-country (gravel) | 0.025 | Estimated from Handbook (2011); Chen et al. (2016) |

This modification is done by the `CRRModifier` class (or the inline code in the production scripts) by parsing the `.veh` file and replacing the value after the `c Fr0` comment line.

**Important:** This modification writes to the `.veh` files directly. In parallel execution, ensure CRR modification is done **before** launching worker processes, not inside them, to avoid race conditions.
