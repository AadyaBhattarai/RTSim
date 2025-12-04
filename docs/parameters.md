# Simulation Parameters

## Important Note

**All parameters below are examples and can be customized by the user.** The only fixed values are the road types which correspond to specific rolling resistance coefficients (CRR).

## Customizable Parameters

| Parameter | Example Values | Description |
|-----------|----------------|-------------|
| `models` | Model1, Model2, etc. | User-defined names matching PHEMlight emission files and route templates |
| `truck_counts` | 1, 2, 3 | Number of trucks (platoon size) |
| `sigma_tau_pairs` | (0.5, 1.0), (0.0, 0.8), etc. | Driver imperfection (sigma) and reaction time (tau) pairs |
| `accel_values` | 0.2, 0.6, 1.0 | Maximum acceleration (m/s²) |
| `speeds_km_h` | 30, 60, 90, 100 | Target speed (km/h) |
| `min_gap_values` | 5, 10, 15, 20 | Minimum gap between vehicles (m) |
| `slope_values` | 0.0, 0.04, 0.08, etc. | Road grade (modified in OpenDRIVE file) |
| `trials` | 10, 30, etc. | Number of simulation runs per scenario |

## What is a "Model"?

A "Model" is simply a vehicle type whose features are defined in:
1. A **PHEMlight emission file** - defines vehicle emissions characteristics
2. A **route file template** - defines vehicle type with length, width, weight, etc.

You can create your own models by:
1. Creating/modifying PHEMlight `.veh` files for your vehicle type
2. Creating route file templates with appropriate `<vType>` definitions
3. Organizing them in the expected folder structure

## Fixed Parameters: Road Types and CRR

The only fixed values are rolling resistance coefficients tied to road surface types:

| Road Type | CRR Value | Description |
|-----------|-----------|-------------|
| `primary` | 0.006923 (default) | Smooth asphalt highway |
| `secondary` | 0.010 | Standard paved road |
| `cross_country` | 0.025 | Unpaved/rough surface |

These CRR values are written to the PHEMlight `.veh` files before simulation.

## Configuring Your Own Experiment

To run with your own parameters, modify the values in the script:

```python
# Example: Custom parameters
models = ["MyTruck", "MyTrailer"]  # Your model folder names
truck_counts = [1, 2, 4]           # Your platoon sizes
speeds_km_h = [50, 70, 110]        # Your test speeds
slope_values = [0.0, 0.05, 0.10]   # Your test slopes
```

## Output Metrics
