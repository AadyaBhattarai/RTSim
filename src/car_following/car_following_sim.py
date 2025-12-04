"""
Car following simulation using SUMO's built-in car following model.

Inherits from SimulationBase for fuel tracking and result collection.
No Plexe required - vehicles use SUMO's Krauss model.
"""

from typing import Dict, List, Any

import traci

# Import from core
from ..core.simulation_base import SimulationBase
from ..core.route_generator import RouteGenerator


class CarFollowingSim(SimulationBase):
    """
    Car following simulation class using SUMO's built-in model.
    
    Inherits fuel tracking and result collection from SimulationBase.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.vehicles: List[str] = []
        
    def setup_vehicles(self) -> None:
        """
        Vehicles are defined in route file for car following.
        Just track vehicle IDs as they appear.
        """
        pass  # Vehicles come from route file
    
    def run_step(self) -> None:
        """Execute one simulation step - just track fuel consumption."""
        # Track all vehicles that appear
        for vid in traci.vehicle.getIDList():
            if vid not in self.vehicles:
                self.vehicles.append(vid)
        
        # Use inherited fuel tracking from SimulationBase
        self.track_fuel_consumption()
        self.step += 1


def run_car_following_simulation(cfg: str, route: str, seed: int) -> List[Dict[str, Any]]:
    """
    Run a complete car following simulation.
    
    Args:
        cfg: Path to SUMO configuration file
        route: Path to route file
        seed: Random seed for SUMO
        
    Returns:
        List of result dictionaries
    """
    # Parse route parameters using RouteGenerator's static method
    params = RouteGenerator.parse_car_following_route(route)
    if not params:
        raise ValueError(f"Bad route: {route}")
    
    # Create simulation instance
    sim = CarFollowingSim({
        'truck_count': params['truck_count'],
        'sigma': params['sigma'],
        'tau': params['tau'],
        'accel': params['accel'],
        'speed': params['speed'],
        'minGap': params['minGap'],
    })
    
    # Start SUMO with seed
    sumo_cmd = ["sumo", "-c", cfg, "--seed", str(seed)]
    traci.start(sumo_cmd)
    
    # Run simulation loop
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        sim.run_step()
    
    traci.close()
    
    # Collect results using inherited method from SimulationBase
    metadata = {
        'Model': params['model'],
        'Count': params['truck_count'],
        'Sigma': params['sigma'],
        'Tau': params['tau'],
        'Accel': params['accel'],
        'Speed': params['speed'],
        # 'minGap': params['minGap'],  # Commented out like in original
    }
    
    return sim.collect_results('car_following', metadata)
