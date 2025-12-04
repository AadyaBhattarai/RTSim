"""
Platooning simulation using Plexe CACC controller.

Inherits from SimulationBase for fuel tracking and result collection.
Uses utils7 for vehicle addition and communication.
"""

import random
from typing import Dict, List, Any

import traci
from plexe import Plexe, CACC

# Import from utils7 (plexe-pyapi)
from utils7 import add_platooning_vehicle, start_sumo, communicate

# Import from core
from ..core.simulation_base import SimulationBase
from ..core.route_generator import RouteGenerator


class PlatooningSim(SimulationBase):
    """
    Platooning simulation class using CACC controller.
    
    Inherits fuel tracking and result collection from SimulationBase.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.plexe = None
        self.topology: Dict[str, Dict[str, str]] = {}
        self.vehicles: List[str] = []
        
    def setup_vehicles(self) -> None:
        """Set up platoon vehicles using utils7's add_platooning_vehicle."""
        n = self.config.get('truck_count', 1)
        distance = self.config.get('min_gap', 5.0)
        speed = self.config.get('speed', 25.0)  # m/s
        tau = self.config.get('tau', 0.8)
        length = self.config.get('length', 10.0)
        sigma = self.config.get('sigma', 0.0)
        accel = self.config.get('accel', 0.5)
        
        delta_t = traci.simulation.getDeltaT()
        depart_speed = speed + sigma * accel * delta_t
        
        self.topology = {}
        self.vehicles = []
        
        for i in range(n):
            vid = f"v.0.{i}"
            self.vehicles.append(vid)
            depart_pos = (n - i + 1) * (distance + length)
            
            # Use utils7's add_platooning_vehicle
            add_platooning_vehicle(
                self.plexe, vid, depart_pos, 0, depart_speed, tau, distance,
                real_engine=False
            )
            
            self.plexe.set_fixed_lane(vid, 0, False)
            traci.vehicle.setSpeedMode(vid, 0)
            self.plexe.use_controller_acceleration(vid, False)
            self.plexe.set_active_controller(vid, CACC)
            self.plexe.set_acc_headway_time(vid, tau)
            
            if i > 0:
                self.topology[vid] = {"front": f"v.0.{i-1}", "leader": "v.0.0"}
            else:
                self.topology[vid] = {}
    
    def run_step(self) -> None:
        """Execute one simulation step with communication and speed control."""
        # Communication every 10 steps using utils7's communicate
        if self.step % 10 == 1 and self._leader_exists():
            communicate(self.plexe, self.topology)
            
        # Speed adjustment every 10 steps
        if self.step % 10 == 0 and self._leader_exists():
            self._apply_speed_variation()
        
        # Use inherited fuel tracking from SimulationBase
        self.track_fuel_consumption()
        self.step += 1
        
    def _leader_exists(self) -> bool:
        """Check if the platoon leader is still in the simulation."""
        return 'v.0.0' in traci.vehicle.getIDList()
    
    def _apply_speed_variation(self) -> None:
        """Apply speed variation to all vehicles in the platoon."""
        base_speed = self.config.get('speed', 25.0)
        sigma = self.config.get('sigma', 0.0)
        accel = self.config.get('accel', 0.5)
        delta_t = traci.simulation.getDeltaT()
        
        variation = sigma * random.uniform(0, accel * delta_t)
        new_speed = base_speed - variation
        
        for vid in self.vehicles:
            if vid in traci.vehicle.getIDList():
                traci.vehicle.setSpeed(vid, new_speed)


def run_platooning_simulation(cfg: str, route: str, speed: float) -> List[Dict[str, Any]]:
    """
    Run a complete platooning simulation.
    
    Args:
        cfg: Path to SUMO configuration file
        route: Path to route file
        speed: Target speed in km/h
        
    Returns:
        List of result dictionaries
    """
    # Parse route parameters using RouteGenerator's static method
    params = RouteGenerator.parse_platooning_route(route)
    if not params:
        raise ValueError(f"Bad route: {route}")
    
    # Create simulation instance with config
    sim = PlatooningSim({
        'truck_count': params['truck_count'],
        'min_gap': params['minGap'],
        'tau': params['tau'],
        'accel': params['accel'],
        'length': params['length'],
        'sigma': params['sigma'],
        'speed': speed / 3.6,  # Convert to m/s
    })
    
    # Start SUMO using utils7's start_sumo
    start_sumo(cfg, False, False)
    
    # Initialize Plexe
    sim.plexe = Plexe()
    traci.addStepListener(sim.plexe)
    
    # Setup vehicles
    sim.setup_vehicles()
    
    # Run simulation loop
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        sim.run_step()
    
    traci.close()
    
    # Collect results using inherited method from SimulationBase
    metadata = {
        'Model': params['model'],
        'Count': params['truck_count'],
        'minGap': params['minGap'],
        'Tau': params['tau'],
        'Accel': params['accel'],
        'Sigma': params['sigma'],
        'Speed': speed,
    }
    
    return sim.collect_results('platooning', metadata)
