"""Main platooning simulation module."""
import traci
import numpy as np
import random
from typing import Dict, List
from plexe import Plexe, CACC

from ..utils.statistics import calculate_confidence_interval

class PlatooningSimulation:
    """Manages platooning vehicle simulations."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.plexe = None
        self.topology = {}
        self.cumulative_fuel = {}
        self.cumulative_distance = {}
    
    def run(self, cfg_path: str, route_params: Dict, speed: float) -> List[Dict]:
        """
        Run a single platooning simulation.
        
        Args:
            cfg_path: Path to SUMO configuration file
            route_params: Dictionary containing route parameters
            speed: Target speed in km/h
            
        Returns:
            List of result dictionaries for each vehicle
        """
        # Initialize SUMO and Plexe
        self._initialize_simulation(cfg_path)
        
        # Add vehicles
        self._add_vehicles(route_params, speed)
        
        # Run simulation loop
        self._simulation_loop(route_params, speed)
        
        # Collect and return results
        return self._collect_results(route_params, speed)
    
    def _initialize_simulation(self, cfg_path: str):
        """Initialize SUMO and Plexe."""
        from utils7 import start_sumo  # Your existing utility
        start_sumo(cfg_path, False, False)
        self.plexe = Plexe()
        traci.addStepListener(self.plexe)
    
    def _add_vehicles(self, params: Dict, speed: float):
        """Add platooning vehicles to simulation."""
        from utils7 import add_platooning_vehicle
        
        n = params['n']
        distance = params['minGap']
        length = params['length']
        tau = params['tau']
        dSpeed = (speed / 3.6) + params['sigma'] * params['accel'] * traci.simulation.getDeltaT()
        
        for i in range(n):
            vid = f"v.0.{i}"
            depart_pos = (n - i + 1) * (distance + length)
            
            add_platooning_vehicle(
                self.plexe, vid, depart_pos, 0, dSpeed, tau, distance, real_engine=False
            )
            
            self.plexe.set_fixed_lane(vid, 0, False)
            traci.vehicle.setSpeedMode(vid, 0)
            self.plexe.use_controller_acceleration(vid, False)
            self.plexe.set_active_controller(vid, CACC)
            self.plexe.set_acc_headway_time(vid, tau)
            
            # Set topology
            if i > 0:
                self.topology[vid] = {"front": f"v.0.{i-1}", "leader": "v.0.0"}
            else:
                self.topology[vid] = {}
    
    # ... (continue with other methods)
