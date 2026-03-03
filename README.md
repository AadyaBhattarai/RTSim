# RTSim: A comprehensive road trip simulator

A comprehensive framework for simulating vehicle platooning and car-following behavior with various levels of autonomy using SUMO (Simulation of Urban MObility) with PHEMLight emission models and Plexe for cooperative adaptive cruise control.

## Features

- **Dual Simulation Modes**: Support for both car-following and platooning scenarios
- **Multi-Parameter Analysis**: Comprehensive testing across slopes, speeds, road types, and vehicle configurations
- **Parallel Processing**: Efficient multi-core execution for large-scale experiments
- **Rolling Resistance Modeling**: Dynamic CRR (Coefficient of Rolling Resistance) modification for different road types
- **Statistical Analysis**: Automated confidence interval calculation and result aggregation
- **Flexible Network Generation**: OpenDRIVE-based network generation with configurable slope profiles

## Table of Contents

- [Installation](#installation)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)

## Prerequisites

### Required Software

- **SUMO** (>= 1.12.0): [Installation Guide](https://sumo.dlr.de/docs/Installing/index.html)
- **Python** (>= 3.8)
- **Plexe**: [GitHub Repository](https://github.com/michele-segata/plexe-pyapi)

### System Requirements

- Linux/Ubuntu (tested on Ubuntu 20.04+)
- Minimum 8GB RAM (16GB recommended for parallel processing)
- Multi-core processor recommended for parallel simulations

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/vehicle-platooning-simulation.git
cd vehicle-platooning-simulation
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Plexe

```bash
# Clone Plexe repository
git clone https://github.com/michele-segata/plexe-pyapi.git
cd plexe-pyapi
pip install -e .
cd ..
```

### 4. Configure SUMO Paths

Edit `config/default_config.yaml` to set your SUMO installation paths:

```yaml
paths:
  sumo_home: "/usr/share/sumo"  # Adjust to your SUMO installation
  base_phem_dir: "/usr/share/sumo/data/emissions"  # PHEMLight emission data
```

### 5. Verify Installation

```bash
python scripts/verify_installation.py
```

## Quick Start

### Run a Simple Platooning Simulation

```bash
python examples/simple_platooning.py
```

### Run a Car Following Simulation

```bash
python examples/simple_car_following.py
```

### Run Full Experiments

```bash
# Platooning experiment
python scripts/run_platooning_experiment.py --config config/experiment_configs/platooning_default.yaml

# Car following experiment
python scripts/run_car_following_experiment.py --config config/experiment_configs/car_following_default.yaml
```

## 📁 Project Structure

```
vehicle-platooning-simulation/
├── README.md                          # This file
├── LICENSE                            # License information
├── requirements.txt                   # Python dependencies
├── setup.py                          # Package installation script
├── .gitignore                        # Git ignore rules
│
├── config/                           # Configuration files
│   ├── default_config.yaml          # Default configuration
│   └── experiment_configs/          # Experiment-specific configs
│       ├── platooning_default.yaml
│       └── car_following_default.yaml
│
├── data/                            # Data files (not tracked in git)
│   ├── opendrive/                   # OpenDRIVE road network files
│   │   ├── experiment_e.xodr       # Base road network
│   │   └── README.md               # OpenDRIVE documentation
│   ├── sumo/                        # SUMO-specific files
│   │   ├── networks/               # Generated network files
│   │   ├── routes/                 # Route definition files
│   │   │   ├── car_following/
│   │   │   └── platooning/
│   │   └── configs/                # SUMO configuration files
│   │       └── grade0.sumocfg
│   └── emissions/                   # PHEMLight emission data
│
├── src/                             # Source code
│   ├── __init__.py
│   ├── core/                        # Core simulation modules
│   │   ├── __init__.py
│   │   ├── simulation_base.py      # Base simulation class
│   │   ├── network_generator.py    # Network generation utilities
│   │   └── route_generator.py      # Route file generation
│   ├── platooning/                  # Platooning-specific code
│   │   ├── __init__.py
│   │   ├── platooning_sim.py       # Platooning simulation
│   │   └── platoon_controller.py   # Platoon control logic
│   ├── car_following/               # Car following code
│   │   ├── __init__.py
│   │   └── car_following_sim.py    # Car following simulation
│   └── utils/                       # Utility modules
│       ├── __init__.py
│       ├── config_loader.py        # Configuration management
│       ├── file_utils.py           # File I/O utilities
│       ├── crr_modifier.py         # Rolling resistance modification
│       ├── statistics.py           # Statistical analysis
│       └── excel_writer.py         # Excel output handling
│
├── scripts/                         # Executable scripts
│   ├── run_platooning_experiment.py    # Main platooning script
│   ├── run_car_following_experiment.py # Main car following script
│   ├── generate_networks.py            # Network generation script
│   └── verify_installation.py          # Installation verification
│
├── examples/                        # Example usage scripts
│   ├── simple_platooning.py
│   └── simple_car_following.py
│
├── tests/                           # Unit tests
│   ├── __init__.py
│   ├── test_network_generator.py
│   ├── test_route_generator.py
│   └── test_crr_modifier.py
│
├── docs/                            # Documentation
│   ├── installation.md             # Detailed installation guide
│   ├── usage.md                    # Usage instructions
│   ├── parameters.md               # Parameter descriptions
│   ├── opendrive_guide.md          # OpenDRIVE format guide
│   └── sumo_configuration.md       # SUMO configuration details
│
└── results/                         # Output directory (git-ignored)
    └── .gitkeep
```

## Usage

### Platooning Simulation

The platooning simulation implements CACC (Cooperative Adaptive Cruise Control) using the Plexe framework:

```python
from src.platooning import PlatooningSimulation
from src.utils.config_loader import load_config

# Load configuration
config = load_config('config/experiment_configs/platooning_default.yaml')

# Initialize simulation
sim = PlatooningSimulation(config)

# Run simulation
results = sim.run_experiment()
```

### Car Following Simulation

The car-following simulation uses SUMO's built-in car-following models:

```python
from src.car_following import CarFollowingSimulation
from src.utils.config_loader import load_config

# Load configuration
config = load_config('config/experiment_configs/car_following_default.yaml')

# Initialize simulation
sim = CarFollowingSimulation(config)

# Run simulation
results = sim.run_experiment()
```

### Key Parameters

#### Vehicle Parameters
- `truck_counts`: Number of vehicles in platoon/convoy (e.g., [1, 2, 3])
- `minGap`: Minimum gap between vehicles (meters)
- `models`: Vehicle emission classes (Model1-Model5)

#### Driver Behavior Parameters
- `sigma`: Driver imperfection (0.0 = perfect, 1.0 = imperfect)
- `tau`: Reaction time (seconds)
- `accel`: Maximum acceleration (m/s²)
- `speeds_km_h`: Target speeds (km/h)

#### Road Parameters
- `slopes`: Road gradient values (0.00-0.20)
- `road_types`: Surface types (primary, secondary, cross_country)
- `crr_values`: Rolling resistance coefficients per road type

## ⚙️ Configuration

### YAML Configuration File Structure

```yaml
simulation:
  trials: 20                    # Number of Monte Carlo trials
  max_workers: null            # CPU cores (null = all available)

network:
  input_xodr: "data/opendrive/experiment_e.xodr"
  slopes: [0.00, 0.04, 0.08, 0.12, 0.16, 0.20]

vehicles:
  models: ["Model1", "Model2"]
  truck_counts: [1, 2]
  minGap_values: [5, 10, 15, 20]

parameters:
  sigma_tau_pairs:
    - [0.5, 1.00]
    - [0.3, 0.90]
    - [0.0, 0.80]
  accel_values: [0.2, 0.6, 1.0]
  speeds_km_h: [30, 60, 90]

roads:
  types: ['primary', 'secondary', 'cross_country']
  crr_values:
    primary: null
    secondary: 0.010
    cross_country: 0.025
```

## Output Files

Simulation results are saved in Excel format:

- **Raw Data**: `results/[experiment_name]/all_scenarios_raw.xlsx`
  - Contains individual vehicle measurements from each trial
  
- **Confidence Intervals**: `results/[experiment_name]/confidence_intervals.xlsx`
  - Statistical summary with 95% confidence intervals
  - Grouped by scenario parameters

### Output Columns

| Column | Description |
|--------|-------------|
| Scenario | Simulation type (platooning/car_following) |
| Model | Vehicle emission class |
| Count | Number of vehicles |
| Slope | Road gradient |
| Speed | Target speed (km/h) |
| Fuel_L_per_100km | Fuel consumption (L/100km) |
| Mean | Average fuel consumption |
| CI_Lower | Lower confidence bound |
| CI_Upper | Upper confidence bound |

## Documentation

Detailed documentation is available in the `docs/` directory:

- **[Installation Guide](docs/installation.md)**: Step-by-step installation instructions
- **[Usage Guide](docs/usage.md)**: Comprehensive usage examples
- **[Parameters Reference](docs/parameters.md)**: Detailed parameter descriptions
- **[OpenDRIVE Guide](docs/opendrive_guide.md)**: Road network design
- **[SUMO Configuration](docs/sumo_configuration.md)**: SUMO setup details

## Research Applications

This framework is designed for research in:

- Vehicle platooning efficiency
- Fuel consumption optimization
- Road grade impact on vehicle performance
- Driver behavior modeling
- Cooperative adaptive cruise control (CACC)
- Traffic flow analysis

## Troubleshooting

### Common Issues

**Issue**: `TraCI connection failed`
```bash
# Solution: Ensure SUMO is installed and in PATH
export SUMO_HOME="/usr/share/sumo"
export PATH="$SUMO_HOME/bin:$PATH"
```

**Issue**: `PHEMLight emission files not found`
```bash
# Solution: Verify PHEMLight data path in config
ls /usr/share/sumo/data/emissions/*.PHEMLight.veh
```

**Issue**: `Import error: No module named 'plexe'`
```bash
# Solution: Reinstall Plexe
pip install git+https://github.com/michele-segata/plexe-pyapi.git
```

## 📝 Citation

If you use this framework in your research, please cite:

```bibtex
@software{vehicle_platooning_sim,
  author = {Your Name},
  title = {Vehicle Platooning and Car Following Simulation Framework},
  year = {2024},
  url = {https://github.com/yourusername/vehicle-platooning-simulation}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or support:
- Email: aadyab@usf.edu

---

**Note**: This is research software. Please validate results against your specific use case before drawing conclusions.
