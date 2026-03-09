"""
Abstract base class for vehicle simulations.

Provides common functionality for both platooning and car-following:
- Fuel consumption tracking per vehicle per timestep
- Distance tracking
- Result collection with metadata
- SUMO config file generation for parallel execution
"""

import os
import re
import secrets
import traci
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class SimulationBase(ABC):
    """
    Abstract base class for vehicle simulations.

    Subclasses must implement:
        setup_vehicles() - define how vehicles enter the simulation
        run_step()       - define per-timestep logic
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.cumulative_fuel_consumption: Dict[str, float] = {}
        self.cumulative_distance: Dict[str, float] = {}
        self.step = 0

    @abstractmethod
    def setup_vehicles(self) -> None:
        """Set up vehicles for the simulation. Implemented by subclasses."""
        pass

    @abstractmethod
    def run_step(self) -> None:
        """Execute one simulation step. Implemented by subclasses."""
        pass

    def reset(self) -> None:
        """Reset simulation state for a new run."""
        self.cumulative_fuel_consumption = {}
        self.cumulative_distance = {}
        self.step = 0

    def track_fuel_consumption(self) -> None:
        """
        Track fuel consumption and distance for all active vehicles.

        Called once per timestep. Fuel is reported by SUMO in mg/s;
        we accumulate mg and convert to litres at collection time.
        """
        delta_t = traci.simulation.getDeltaT()

        for veh_id in traci.vehicle.getIDList():
            if veh_id not in self.cumulative_fuel_consumption:
                self.cumulative_fuel_consumption[veh_id] = 0.0
                self.cumulative_distance[veh_id] = 0.0

            fuel_mg = traci.vehicle.getFuelConsumption(veh_id) * delta_t
            distance_km = traci.vehicle.getDistance(veh_id) / 1000.0

            if distance_km > 0:
                self.cumulative_fuel_consumption[veh_id] += fuel_mg
                self.cumulative_distance[veh_id] = distance_km

    def calculate_fuel_efficiency(self, veh_id: str) -> Optional[float]:
        """
        Calculate fuel efficiency in L/100km for a vehicle.

        Diesel density: 850 g/L = 850,000 mg/L
        """
        km = self.cumulative_distance.get(veh_id, 0.0)
        if km <= 0:
            return None
        fuel_litres = self.cumulative_fuel_consumption[veh_id] / 850000.0
        return (fuel_litres / km) * 100

    def collect_results(self, scenario: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect simulation results for all tracked vehicles.

        Args:
            scenario: 'platooning' or 'car_following'
            metadata: Additional columns to include in each result row
        """
        results = []
        for veh_id in self.cumulative_fuel_consumption:
            km = self.cumulative_distance.get(veh_id, 0.0)
            result = {
                'Scenario': scenario,
                'Vehicle': veh_id,
                'Fuel_L_per_100km': self.calculate_fuel_efficiency(veh_id),
                'Distance_km': km,
            }
            result.update(metadata)
            results.append(result)
        return results

    @staticmethod
    def generate_config(cfg_file: str, route_file: str, net_file: str) -> str:
        """
        Generate a unique temporary SUMO configuration file.

        Needed for parallel execution — each worker gets its own .sumocfg
        pointing to the correct network and route files.

        Args:
            cfg_file:   Path to the base .sumocfg template
            route_file: Path to the route file for this run
            net_file:   Path to the network file for this run

        Returns:
            Path to the generated temporary .sumocfg file
        """
        with open(cfg_file, 'r') as f:
            content = f.read()

        route_file = route_file.replace('\\', '/')
        net_file = net_file.replace('\\', '/')

        content = re.sub(
            r'<route-files\s+value="[^"]+"',
            f'<route-files value="{route_file}"',
            content
        )
        content = re.sub(
            r'<net-file\s+value="[^"]+"',
            f'<net-file value="{net_file}"',
            content
        )

        temp_cfg = f"sumo_{secrets.token_hex(8)}.sumocfg"
        with open(temp_cfg, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        return temp_cfg
