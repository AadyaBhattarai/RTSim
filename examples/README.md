# Example Folder Structure

This folder contains example files showing the required folder structure for platooning simulations.

## Folder Structure Overview

```
simulation/                          ← Route templates base directory
├── Model1/                          ← Vehicle model (user-defined name)
│   ├── 1truck/                      ← Single truck (no gap subfolder)
│   │   └── 90/                      ← Speed (km/h)
│   │       ├── lower/               ← Lower drag value
│   │       │   └── grade01.rou.xml  ← Route file
│   │       └── upper/               ← Upper drag value
│   │           └── grade01.rou.xml
│   │
│   ├── 2truck/                      ← 2-truck platoon
│   │   └── 90/                      ← Speed (km/h)
│   │       ├── 5/                   ← Gap = 5 meters
│   │       │   ├── lower/
│   │       │   │   └── grade01.rou.xml
│   │       │   └── upper/
│   │       │       └── grade01.rou.xml
│   │       ├── 10/                  ← Gap = 10 meters
│   │       ├── 15/                  ← Gap = 15 meters
│   │       └── 20/                  ← Gap = 20 meters
│   │
│   └── 3truck/                      ← 3-truck platoon (same structure as 2truck)
│
├── Model2/
├── Model3/
├── Model4/
└── Model5/


PHEMlight/                           ← Emissions data directory
├── Model1/
│   └── 2truck/
│       └── 5/
│           └── 90/
│               ├── Lower/           ← Lower drag coefficient files
│               │   ├── RT_II_D_EU0.veh
│               │   └── RT_II_D_EU1.veh
│               └── Upper/           ← Upper drag coefficient files
│                   ├── RT_II_D_EU0.veh
│                   └── RT_II_D_EU1.veh
```

## Why Lower and Upper?

Since exact drag coefficient values are not always known, we run simulations with:
- **Lower**: Lower bound estimate of drag coefficient
- **Upper**: Upper bound estimate of drag coefficient

This gives a range of fuel consumption results.

## Route File → PHEMlight Connection

In the route file, each `<vType>` has an `emissionClass` attribute that points to the PHEMlight folder:

```xml
<vType id="vtypeauto1" 
       length="6.534"
       ...
       emissionClass="PHEMlight/Model1/2truck/5/90/Lower/RT_II_D_EU0"/>
```

This tells SUMO to use the emission data from:
```
PHEMlight/Model1/2truck/5/90/Lower/RT_II_D_EU0.veh
```

## PHEMlight .veh File

The `.veh` file contains vehicle parameters including:
- Vehicle mass
- Cross section area
- Air drag coefficient (CdA)
- Rolling resistance coefficient (Fr0) ← **This is modified for different road types**

Example `.veh` file:
```
c Rolling resistance coefficient [-]
c Fr0
0.006923
```

The simulation code modifies `Fr0` (CRR) based on road type:
- primary: 0.006923 (default)
- secondary: 0.010
- cross_country: 0.025

## Key Points

1. **Model** = folder name that matches between simulation/ and PHEMlight/
2. **1truck** has no gap subfolder (single vehicle)
3. **2truck, 3truck** have gap subfolders (5, 10, 15, 20 meters)
4. **lower/upper** separate drag coefficient variants
5. **emissionClass** in route file must match PHEMlight folder path
