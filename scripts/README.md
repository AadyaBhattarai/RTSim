# Scripts

Production scripts for running large-scale experiments with parallel processing and progress tracking.

## Scripts

| Script | Description |
|--------|-------------|
| `run_platooning.py` | Run platooning experiments (uses Plexe) |
| `run_car_following.py` | Run car following experiments (SUMO only) |

---

## Platooning Script

### Usage

```bash
# Show help
python scripts/run_platooning.py --help

# Dry run (show configuration without running)
python scripts/run_platooning.py \
    --xodr-file /path/to/experiment.xodr \
    --sumo-cfg /path/to/grade0.sumocfg \
    --route-base-dir /path/to/simulation/ \
    --phem-dir /path/to/PHEMlight/ \
    --dry-run

# Run experiment
python scripts/run_platooning.py \
    --xodr-file /path/to/experiment.xodr \
    --sumo-cfg /path/to/grade0.sumocfg \
    --route-base-dir /path/to/simulation/ \
    --phem-dir /path/to/PHEMlight/ \
    --trials 30 \
    --workers 50 \
    --output-dir results/platooning
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `--xodr-file` | Path to your OpenDRIVE (.xodr) file |
| `--sumo-cfg` | Path to your base SUMO config (.sumocfg) file |
| `--route-base-dir` | Path to platooning route templates (e.g., `simulation/`) |
| `--phem-dir` | Path to PHEMlight emissions folder |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--output-dir`, `-o` | `platooning_results` | Output directory |
| `--trials`, `-t` | `30` | Number of trials per scenario |
| `--workers`, `-w` | CPU count | Number of parallel workers |
| `--dry-run` | - | Show configuration without running |

### Output Files

```
platooning_results/
├── networks/              # Generated network files
├── routes/                # Generated route files
├── platooning_raw.xlsx    # Raw results from all trials
└── platooning_ci.xlsx     # Confidence intervals
```

---

## Car Following Script

### Usage

```bash
# Show help
python scripts/run_car_following.py --help

# Dry run
python scripts/run_car_following.py \
    --xodr-file /path/to/experiment.xodr \
    --sumo-cfg /path/to/grade0.sumocfg \
    --route-base-dir /path/to/carfollowing/ \
    --phem-dir /path/to/emissions/ \
    --dry-run

# Run experiment
python scripts/run_car_following.py \
    --xodr-file /path/to/experiment.xodr \
    --sumo-cfg /path/to/grade0.sumocfg \
    --route-base-dir /path/to/carfollowing/ \
    --phem-dir /path/to/emissions/ \
    --trials 10 \
    --workers 50 \
    --output-dir results/car_following
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `--xodr-file` | Path to your OpenDRIVE (.xodr) file |
| `--sumo-cfg` | Path to your base SUMO config (.sumocfg) file |
| `--route-base-dir` | Path to car following route templates (e.g., `carfollowing/`) |
| `--phem-dir` | Path to emissions folder |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--output-dir`, `-o` | `car_following_results` | Output directory |
| `--trials`, `-t` | `10` | Number of trials per scenario |
| `--workers`, `-w` | `50` | Number of parallel workers |
| `--dry-run` | - | Show configuration without running |

### Output Files

```
car_following_results/
├── networks/                          # Generated network files
├── routes/                            # Generated route files
├── all_scenarios_raw.xlsx             # Raw results from all trials
├── confidence_intervals_Model4.xlsx   # CI for Model4
└── confidence_intervals_Model5.xlsx   # CI for Model5
```

---

## Modifying Parameters

Parameters are defined at the top of each script's `main()` function. Edit these as needed:

### Platooning Parameters (run_platooning.py)

```python
models = ["Model1", "Model2", "Model3", "Model4", "Model5"]
truck_counts = [1, 2, 3]
sigma_tau_pairs = [(0.5, 1.00), (0.4, 0.95), ...]
accel_values = [0.2, 0.4, 0.6, 0.8, 1.0]
speeds_km_h = [30, 40, 60, 80, 90, 100]
min_gap_values = [5.0, 10.0, 15.0, 20.0]
slope_values = [0.0, 0.04, 0.06, 0.08, 0.10, 0.12, 0.16, 0.20]
road_types = ['primary', 'secondary', 'cross_country']
```

### Car Following Parameters (run_car_following.py)

```python
models = ["Model4", "Model5"]
truck_counts = [1]
sigma_tau_pairs = [(0.5, 1.00), (0.4, 0.95), ...]
accel_values = [0.2, 0.6, 1.0]
speeds_km_h = [30, 60, 90, 100]
min_gap_values = [5, 10, 15, 20]
slope_values = [0.0, 0.06, 0.08, 0.16, 0.20]
road_types = ['cross_country']
```

---

## Key Differences

| Feature | Platooning | Car Following |
|---------|------------|---------------|
| Uses Plexe | Yes | No |
| PHEMlight suffix | `.veh` | `.PHEMLight.veh` |
| Route template | `grade01.rou.xml` | `grade2.rou.xml` |
| CI output | Single file | Per-model files |
| Default trials | 30 | 10 |
| Randomization | Python random | SUMO --seed |

---

## Example: Full Run

```bash
# 1. Activate conda environment
conda activate sumo_env

# 2. Run platooning experiment
python scripts/run_platooning.py \
    --xodr-file ~/data/experiment_e.xodr \
    --sumo-cfg ~/data/grade0.sumocfg \
    --route-base-dir ~/data/simulation/ \
    --phem-dir ~/data/PHEMlight/ \
    --trials 30 \
    --workers 50 \
    --output-dir ~/results/platooning

# 3. Run car following experiment
python scripts/run_car_following.py \
    --xodr-file ~/data/experiment_e.xodr \
    --sumo-cfg ~/data/grade0.sumocfg \
    --route-base-dir ~/data/carfollowing/ \
    --phem-dir ~/data/emissions/ \
    --trials 10 \
    --workers 50 \
    --output-dir ~/results/car_following
```
