"""
Abstract base class for vehicle simulations.

Works for both platooning and car following simulations.
Provides common functionality: fuel tracking, result collection, config generation.
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
    
    Subclasses: PlatooningSim, CarFollowingSim
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: Configuration dictionary containing simulation parameters
        """
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
        """Track fuel consumption and distance for all vehicles."""
        vehicle_ids = traci.vehicle.getIDList()
        delta_t = traci.simulation.getDeltaT()
        
        for veh_id in vehicle_ids:
            if veh_id not in self.cumulative_fuel_consumption:
                self.cumulative_fuel_consumption[veh_id] = 0.0
                self.cumulative_distance[veh_id] = 0.0
                
            fuel = traci.vehicle.getFuelConsumption(veh_id) * delta_t
            distance_km = traci.vehicle.getDistance(veh_id) / 1000.0
            
            if distance_km > 0:
                self.cumulative_fuel_consumption[veh_id] += fuel
                self.cumulative_distance[veh_id] = distance_km
                
    def calculate_fuel_efficiency(self, veh_id: str) -> Optional[float]:
        """
        Calculate fuel efficiency in L/100km for a vehicle.
        
        Returns:
            Fuel consumption in L/100km or None if distance is zero
        """
        km = self.cumulative_distance.get(veh_id, 0.0)
        if km <= 0:
            return None
        # Diesel density: 850 g/L = 850000 mg/L
        fuel_liters = self.cumulative_fuel_consumption[veh_id] / 850000.0
        return (fuel_liters / km) * 100
    
    def collect_results(self, scenario: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect simulation results for all vehicles.
        
        Args:
            scenario: Name of the simulation scenario ('platooning' or 'car_following')
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
    
    @staticmethod
    def generate_config(cfg_file: str, route_file: str, net_file: str, unique: bool = True) -> str:
        """
        Generate a temporary SUMO configuration file.
        
        Args:
            cfg_file: Base configuration file path
            route_file: Route file path
            net_file: Network file path
            unique: If True, generate unique filename for parallel execution
            
        Returns:
            Path to the generated configuration file
        """
        with open(cfg_file, 'r') as f:
            cfg_content = f.read()
            
        route_file = route_file.replace('\\', '/')
        net_file = net_file.replace('\\', '/')
        
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
        
        if unique:
            temp_cfg = f"sumo_{secrets.token_hex(8)}.sumocfg"
        else:
            temp_cfg = "temp.sumocfg"
            
        with open(temp_cfg, 'w', encoding='utf-8') as f:
            f.write(cfg_content)
            f.flush()
            os.fsync(f.fileno())
            
        return temp_cfg
