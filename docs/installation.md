# Installation Guide

## Prerequisites

- **Conda** (Anaconda or Miniconda)
- **Python 3.8+**

## Step 1: Create Conda Environment

```bash
conda create -n sumo_env python=3.10
conda activate sumo_env
```

## Step 2: Install SUMO via Conda

```bash
conda install -c conda-forge sumo
```

Verify installation:
```bash
sumo --version
```

Set the SUMO_HOME environment variable:
```bash
# Find where conda installed SUMO
export SUMO_HOME="$CONDA_PREFIX/share/sumo"

# Add to your shell config (optional, for persistence)
echo 'export SUMO_HOME="$CONDA_PREFIX/share/sumo"' >> ~/.bashrc
```

## Step 3: Install Plexe (for platooning only)

```bash
git clone https://github.com/michele-segata/plexe-pyapi.git
cd plexe-pyapi
pip install .
cd ..
```

## Step 4: Install This Package

```bash
git clone https://github.com/yourusername/vehicle-platooning-simulation.git
cd vehicle-platooning-simulation
pip install -r requirements.txt
```

## Step 5: Verify Installation

```bash
python -c "from src import SimulationBase, NetworkGenerator, RouteGenerator"
python -c "from src import run_platooning_simulation, run_car_following_simulation"
python -c "import traci; print('TraCI OK')"
```

## Complete Setup Script

```bash
# Create and activate environment
conda create -n sumo_env python=3.10 -y
conda activate sumo_env

# Install SUMO
conda install -c conda-forge sumo -y

# Set SUMO_HOME
export SUMO_HOME="$CONDA_PREFIX/share/sumo"

# Install Plexe
git clone https://github.com/michele-segata/plexe-pyapi.git
cd plexe-pyapi && pip install . && cd ..

# Install this package
git clone https://github.com/yourusername/vehicle-platooning-simulation.git
cd vehicle-platooning-simulation
pip install -r requirements.txt
```

## Troubleshooting

### "traci module not found"
Ensure SUMO_HOME is set correctly:
```bash
export SUMO_HOME="$CONDA_PREFIX/share/sumo"
export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"
```

### "utils module not found"
The `utils.py` file must be in your Python path - this is a custom Plexe wrapper.

### SUMO not found after restarting terminal
Add to your `~/.bashrc`:
```bash
conda activate sumo_env
export SUMO_HOME="$CONDA_PREFIX/share/sumo"
```
