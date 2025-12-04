# SUMO Configuration Guide

## What is a SUMO Configuration File?

A `.sumocfg` file is an XML file that tells SUMO:
- Which **network file** (.net.xml) to use
- Which **route file** (.rou.xml) to use
- Simulation settings (step length, collision handling, GUI options)

It's the main entry point for running a SUMO simulation.

## Example Configuration File (grade0.sumocfg)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="gradef.net.xml"/>
        <route-files value="grade01.rou.xml"/>
        <junction-taz value="true"/>
    </input>
    <time>
        <begin value="0"/>
        <step-length value="0.01"/>
    </time>
    <processing>
        <collision.action value="remove"/>
        <collision.stoptime value="10"/>
    </processing>
    <gui_only>
        <start value="true"/>
        <gui-settings-file value="freeway.gui.xml"/>
        <quit-on-end value="true"/>
    </gui_only>
</configuration>
```

## Configuration Sections Explained

### `<input>` - Input Files
| Parameter | Description |
|-----------|-------------|
| `net-file` | The road network file (.net.xml) |
| `route-files` | The route/vehicle file (.rou.xml) |
| `junction-taz` | Treat junctions as traffic assignment zones |

### `<time>` - Timing
| Parameter | Description |
|-----------|-------------|
| `begin` | Simulation start time (seconds) |
| `step-length` | Time step (0.01 = 10ms precision) |

### `<processing>` - Collision Handling
| Parameter | Description |
|-----------|-------------|
| `collision.action` | What to do on collision (`remove` = remove vehicle) |
| `collision.stoptime` | Time vehicle stops after collision |

### `<gui_only>` - GUI Settings
| Parameter | Description |
|-----------|-------------|
| `start` | Auto-start simulation when GUI opens |
| `gui-settings-file` | GUI appearance settings |
| `quit-on-end` | Close GUI when simulation ends |

## How Our Code Modifies It

The simulation code dynamically updates `net-file` and `route-files` for each scenario:

```python
# From SimulationBase.generate_config()
cfg_content = re.sub(
    r'<route-files\s+value="[^"]+"',
    f'<route-files value="{route_file}"',
    cfg_content
)
cfg_content = re.sub(
    r'<net-file\s+value="[^"]+"',
    f'<net-file value="{net_file}"',
    cfg_content
)
```

This allows running multiple scenarios with different networks and routes from a single base config.

## Running SUMO

### From Command Line
```bash
# Without GUI
sumo -c grade0.sumocfg

# With GUI
sumo-gui -c grade0.sumocfg
```

### From Python (TraCI)
```python
import traci

# Platooning (uses utils7)
from utils7 import start_sumo
start_sumo("grade0.sumocfg", False, False)

# Car Following (direct, with seed for randomization)
traci.start(["sumo", "-c", "grade0.sumocfg", "--seed", "42"])
```

## Files You Need

| File | Description |
|------|-------------|
| `grade0.sumocfg` | Configuration file (entry point) |
| `*.net.xml` | Network file (roads, generated from OpenDRIVE) |
| `*.rou.xml` | Route file (vehicles, routes, vehicle types) |
| `freeway.gui.xml` | GUI settings (optional, for visualization) |

## Workflow

```
experiment_e.xodr          (OpenDRIVE input)
        ↓
    netconvert
        ↓
network_slope_0.08.net.xml (SUMO network)
        +
route_Model1_2truck_...    (Route file)
        +
grade0.sumocfg             (Config file - updated dynamically)
        ↓
      SUMO simulation
        ↓
    Fuel consumption results
```
