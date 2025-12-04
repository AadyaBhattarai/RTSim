"""
Base simulation class providing common functionality for all simulation types.
"""

import os
import re
import traci
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple


class SimulationBase(ABC):
    """
    Abstract base class for vehicle simulations.
    
    Provides common functionality for SUMO-based simulations including
    fuel consumption tracking, distance calculation, and result collection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the simulation base.
        
        Args:
            config: Configuration dictionary containing simulation parameters
        """
        self.config = config
        self.cumulative_fuel_consumption: Dict[str, float] = {}
        self.cumulative_distance: Dict[str, float] = {}
        self.results: List[Dict[str, Any]] = []
        self.step = 0
        
    @abstractmethod
    def setup_vehicles(self) -> Dict[str, Dict[str, str]]:
        """
        Set up vehicles for the simulation.
        
        Returns:
            Dictionary representing the vehicle topology
        """
        pass
    
    @abstractmethod
    def run_step(self) -> None:
        """Execute one simulation step."""
        pass
    
    def start_sumo(self, cfg_file: str, gui: bool = False) -> None:
        """
        Start the SUMO simulation.
        
        Args:
            cfg_file: Path to SUMO configuration file
            gui: Whether to use GUI mode
        """
        sumo_binary = "sumo-gui" if gui else "sumo"
        sumo_cmd = [sumo_binary, "-c", cfg_file, "--start"]
        traci.start(sumo_cmd)
        
    def close_sumo(self) -> None:
        """Close the SUMO simulation."""
        traci.close()
        
    def track_fuel_consumption(self) -> None:
        """
        Track fuel consumption and distance for all vehicles in simulation.
        """
        vehicle_ids = traci.vehicle.getIDList()
        delta_t = traci.simulation.getDeltaT()
        
        for veh_id in vehicle_ids:
            if veh_id not in self.cumulative_fuel_consumption:
                self.cumulative_fuel_consumption[veh_id] = 0.0
                self.cumulative_distance[veh_id] = 0.0
                
            # Get fuel consumption in mg/s and convert to accumulated value
            fuel = traci.vehicle.getFuelConsumption(veh_id) * delta_t
            distance_km = traci.vehicle.getDistance(veh_id) / 1000.0
            
            if distance_km > 0:
                self.cumulative_fuel_consumption[veh_id] += fuel
                self.cumulative_distance[veh_id] = distance_km
                
    def calculate_fuel_efficiency(self, veh_id: str) -> Optional[float]:
        """
        Calculate fuel efficiency in L/100km for a vehicle.
        
        Args:
            veh_id: Vehicle identifier
            
        Returns:
            Fuel consumption in L/100km or None if distance is zero
        """
        km = self.cumulative_distance.get(veh_id, 0.0)
        if km <= 0:
            return None
            
        # Convert mg to liters (assuming diesel density of 850 g/L = 850000 mg/L)
        fuel_liters = self.cumulative_fuel_consumption[veh_id] / 850000.0
        return (fuel_liters / km) * 100
    
    def collect_results(self, scenario: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect simulation results for all vehicles.
        
        Args:
            scenario: Name of the simulation scenario
            metadata: Additional metadata to include in results
            
        Returns:
            List of result dictionaries for each vehicle
        """
        results = []
        
        for veh_id in self.cumulative_fuel_consumption:
            km = self.cumulative_distance.get(veh_id, 0.0)
            fuel_l100km = self.calculate_fuel_efficiency(veh_id)
            
            result = {
                'Scenario': scenario,
                'Vehicle': veh_id,
                'Fuel_L_per_100km': fuel_l100km,
                'Distance_km': km,
            }
            result.update(metadata)
            results.append(result)
            
        return results
    
    def reset(self) -> None:
        """Reset simulation state for a new run."""
        self.cumulative_fuel_consumption = {}
        self.cumulative_distance = {}
        self.results = []
        self.step = 0
        
    @staticmethod
    def parse_route_filename(route_file: str) -> Optional[Dict[str, Any]]:
        """
        Parse parameters from a route filename.
        
        Args:
            route_file: Path to route file
            
        Returns:
            Dictionary of parsed parameters or None if parsing fails
        """
        pattern = re.compile(
            r'^route_(\w+)_(\d+)truck_(lower|upper)_minGap_([\d\.]+)_tau_([\d\.]+)'
            r'_accel_([\d\.]+)_length_([\d\.]+)_sigma_([\d\.]+)\.rou\.xml$'
        )
        
        match = pattern.match(os.path.basename(route_file))
        if not match:
            return None
            
        model, n_str, variant, minGap_str, tau_str, accel_str, length_str, sigma_str = match.groups()
        
        return {
            'model': model,
            'truck_count': int(n_str),
            'variant': variant,
            'minGap': float(minGap_str),
            'tau': float(tau_str),
            'accel': float(accel_str),
            'length': float(length_str),
            'sigma': float(sigma_str),
        }
    
    @staticmethod
    def generate_config(cfg_file: str, route_file: str, net_file: str) -> str:
        """
        Generate a temporary SUMO configuration file.
        
        Args:
            cfg_file: Base configuration file path
            route_file: Route file path
            net_file: Network file path
            
        Returns:
            Path to the generated configuration file
        """
        with open(cfg_file, 'r') as f:
            cfg_content = f.read()
            
        # Normalize path separators
        route_file = route_file.replace('\\', '/')
        net_file = net_file.replace('\\', '/')
        
        # Update route and network file references
        cfg_content = re.sub(
            r'<route-files value="[^"]+"',
            f'<route-files value="{route_file}"',
            cfg_content
        )
        cfg_content = re.sub(
            r'<net-file value="[^"]+"',
            f'<net-file value="{net_file}"',
            cfg_content
        )
        
        temp_cfg = "temp.sumocfg"
        with open(temp_cfg, 'w') as f:
            f.write(cfg_content)
            
        return temp_cfg
