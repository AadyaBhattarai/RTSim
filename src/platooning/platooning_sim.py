"""
Platooning simulation using Plexe ACC/CACC controllers.

Vehicles travel as a coordinated platoon using Plexe's adaptive cruise
control. Each vehicle gets a position-specific drag coefficient via its
PHEMlight emission file (set during file generation, not at runtime).

Automation levels are modeled by varying the amplitude of periodic speed
perturbations applied to the platoon. Higher sigma (driver imperfection)
causes larger speed drops, requiring more acceleration to recover — thus
consuming more fuel. At sigma=0 (full automation), vehicles maintain
steady speed with minimal fuel waste.

Speed perturbation model (applied every 20 simulation steps):
    v_set = v_desired - sigma * uniform(0, accel * eta)
where eta = 0.090 is a smoothing constant.

Requires:
    - Plexe (pip install plexe or from github.com/michele-segata/plexe-pyapi)
    - SUMO with SUMO_HOME environment variable set
"""

import random
from typing import Dict, List, Any

import traci
from plexe import Plexe, ACC

# Plexe utility functions (modified from plexe-pyapi examples)
# See plexe_utils.py for how vehicle IDs map to position-specific vTypes
from .plexe_utils import add_platooning_vehicle, start_sumo, communicate

from ..core.simulation_base import SimulationBase
from ..core.route_generator import RouteGenerator


# Smoothing constant for speed perturbations.
# Chosen to keep induced decelerations within realistic bounds.
SPEED_PERTURBATION_ETA = 0.090


class PlatooningSim(SimulationBase):
    """Platooning simulation using Plexe ACC/CACC."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.plexe = None
        self.topology: Dict[str, Dict[str, str]] = {}
        self.vehicles: List[str] = []

    def setup_vehicles(self) -> None:
        """
        Add platoon vehicles to the simulation using Plexe.

        Each vehicle is placed at a calculated position on the road,
        set to use ACC controller, and assigned to lane 0.
        The topology dict stores leader/front relationships for
        V2V communication via Plexe's communicate() function.
        """
        n = self.config.get('truck_count', 1)
        distance = self.config.get('min_gap', 5.0)
        speed = self.config.get('speed', 25.0)  # m/s
        tau = self.config.get('tau', 0.8)
        length = self.config.get('length', 10.0)

        self.topology = {}
        self.vehicles = []

        for i in range(n):
            vid = f"v.0.{i}"
            self.vehicles.append(vid)
            depart_pos = (n - i + 1) * (distance + length)

            add_platooning_vehicle(
                self.plexe, vid, depart_pos, 0, speed, tau, distance,
                real_engine=False
            )

            self.plexe.set_fixed_lane(vid, 0, False)
            traci.vehicle.setSpeedMode(vid, 0)
            self.plexe.use_controller_acceleration(vid, True)
            self.plexe.set_active_controller(vid, ACC)
            self.plexe.set_acc_headway_time(vid, tau)

            if i > 0:
                self.topology[vid] = {
                    "front": f"v.0.{i-1}",
                    "leader": "v.0.0"
                }
            else:
                self.topology[vid] = {}

    def run_step(self) -> None:
        """
        Execute one simulation step:
        1. V2V communication every 10 steps
        2. Speed perturbation every 20 steps (mimics driver imperfection)
        3. Fuel tracking every step
        """
        if self.step % 10 == 1 and self._leader_exists():
            communicate(self.plexe, self.topology)

        if self.step % 20 == 0 and self._leader_exists():
            self._apply_speed_perturbation()

        self.track_fuel_consumption()
        self.step += 1

    def _leader_exists(self) -> bool:
        """Check if the platoon leader is still in the simulation."""
        return 'v.0.0' in traci.vehicle.getIDList()

    def _apply_speed_perturbation(self) -> None:
        """
        Apply speed perturbation to mimic driver imperfection.

        At sigma=0 (full automation), no perturbation is applied.
        At sigma=0.5 (human driver), significant speed drops occur,
        requiring acceleration to recover — wasting fuel.
        """
        base_speed = self.config.get('speed', 25.0)
        sigma = self.config.get('sigma', 0.0)
        accel = self.config.get('accel', 0.5)

        perturbation = sigma * random.uniform(0, accel * SPEED_PERTURBATION_ETA)
        new_speed = base_speed - perturbation

        for vid in self.topology.keys():
            if vid in traci.vehicle.getIDList():
                self.plexe.set_cc_desired_speed(vid, new_speed)


def run_platooning_simulation(
    cfg: str, route: str, speed: float
) -> List[Dict[str, Any]]:
    """
    Run a complete platooning simulation.

    Args:
        cfg:   Path to SUMO configuration file
        route: Path to route file (parameters encoded in filename)
        speed: Target speed in km/h

    Returns:
        List of result dicts, one per vehicle in the platoon
    """
    params = RouteGenerator.parse_platooning_route(route)
    if not params:
        raise ValueError(f"Cannot parse route filename: {route}")

    sim = PlatooningSim({
        'truck_count': params['truck_count'],
        'min_gap': params['minGap'],
        'tau': params['tau'],
        'accel': params['accel'],
        'length': params['length'],
        'sigma': params['sigma'],
        'speed': speed / 3.6,  # Convert km/h to m/s
    })

    # Start SUMO using Plexe's helper (handles TraCI connection)
    start_sumo(cfg, False, False)

    # Initialize Plexe and register as step listener
    sim.plexe = Plexe()
    traci.addStepListener(sim.plexe)

    # Place vehicles on the road
    sim.setup_vehicles()

    # Run until all vehicles complete their trips
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        sim.run_step()

    traci.close()

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
