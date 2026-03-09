"""
Car-following simulation using SUMO's built-in Krauss model.

Vehicles follow each other using the Krauss car-following model with
parameters sigma (driver imperfection) and tau (reaction time) set in
the route file. Automation levels are implemented by varying these
parameters — lower sigma means less speed fluctuation, lower tau
allows shorter headways.

No Plexe or external controller is needed. SUMO handles all vehicle
dynamics internally. Randomization comes from SUMO's --seed option.

Car-following does NOT consider drag reduction between vehicles.
Any fuel savings come purely from smoother speed control.
"""

import os
import re
from typing import Dict, List, Any

import traci

from ..core.simulation_base import SimulationBase
from ..core.route_generator import RouteGenerator


class CarFollowingSim(SimulationBase):
    """Car-following simulation using SUMO's Krauss model."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

    def setup_vehicles(self) -> None:
        """Vehicles are defined in the route file — nothing to set up."""
        pass

    def run_step(self) -> None:
        """Track fuel consumption for all active vehicles."""
        self.track_fuel_consumption()
        self.step += 1


def run_car_following_simulation(
    cfg: str, route: str, seed: int
) -> List[Dict[str, Any]]:
    """
    Run a complete car-following simulation.

    Args:
        cfg:   Path to SUMO configuration file
        route: Path to route file (parameters encoded in filename)
        seed:  Random seed for SUMO (use trial number)

    Returns:
        List of result dicts, one per vehicle
    """
    params = RouteGenerator.parse_car_following_route(route)
    if not params:
        raise ValueError(f"Cannot parse route filename: {route}")

    sim = CarFollowingSim()

    # Start SUMO with seed for reproducibility
    traci.start(["sumo", "-c", cfg, "--seed", str(seed)])

    # Run until all vehicles have completed their trips
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        sim.run_step()

    traci.close()

    metadata = {
        'Model': params['model'],
        'Count': params['truck_count'],
        'Sigma': params['sigma'],
        'Tau': params['tau'],
        'Accel': params['accel'],
        'Speed': params['speed'],
        'minGap': params['minGap'],
    }

    return sim.collect_results('car_following', metadata)
