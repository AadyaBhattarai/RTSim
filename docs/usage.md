# Usage Guide

## Running Experiments

### Platooning Simulation

```bash
python scripts/run_platooning.py --trials 30 --output-dir results/platooning
```

**Options:**
| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir`, `-o` | `results` | Output directory for results |
| `--trials`, `-t` | `30` | Number of trials per scenario |
| `--workers`, `-w` | CPU count | Number of parallel workers |
| `--xodr-file` | `experiment_e.xodr` | Your OpenDRIVE input file |
| `--sumo-cfg` | `grade0.sumocfg` | Your base SUMO config file |
| `--route-base-dir` | - | Your route templates folder |
| `--phem-dir` | - | Your PHEMlight emissions folder |
| `--dry-run` | - | Show config without running |

**Example:**
```bash
python scripts/run_platooning.py \
    --trials 30 \
    --output-dir my_results \
    --xodr-file /path/to/your/experiment.xodr \
    --sumo-cfg /path/to/your/config.sumocfg \
    --route-base-dir /path/to/your/route/templates \
    --phem-dir /path/to/your/PHEMlight/folder
```

### Car Following Simulation

```bash
python scripts/run_car_following.py --trials 10 --output-dir results/car_following
```

**Options:**
| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir`, `-o` | `car_following_results` | Output directory for results |
| `--trials`, `-t` | `10` | Number of trials per scenario |
| `--workers`, `-w` | `50` | Number of parallel workers |
| `--xodr-file` | `experiment_e.xodr` | Your OpenDRIVE input file |
| `--sumo-cfg` | `grade0.sumocfg` | Your base SUMO config file |
| `--route-base-dir` | - | Your route templates folder |
| `--phem-dir` | - | Your emissions folder |

**Example:**
```bash
python scripts/run_car_following.py \
    --trials 10 \
    --output-dir my_cf_results \
    --route-base-dir /path/to/your/carfollowing/templates \
    --phem-dir /path/to/your/emissions/folder
```

## Dry Run

To see the configuration without running simulations:

```bash
python scripts/run_platooning.py --dry-run
python scripts/run_car_following.py --dry-run
```

## Output Files

### Platooning
| File | Description |
|------|-------------|
| `platooning_raw.xlsx` | Raw results from all trials |
| `platooning_ci.xlsx` | Confidence intervals |

### Car Following
| File | Description |
|------|-------------|
| `all_scenarios_raw.xlsx` | Raw results from all trials |
| `confidence_intervals_{Model}.xlsx` | Per-model confidence interval files |
