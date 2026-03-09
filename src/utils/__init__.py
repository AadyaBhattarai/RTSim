"""RTSim: Road-Trip Simulator for fuel consumption of ICEVs with automation."""

from .core import SimulationBase, NetworkGenerator, RouteGenerator
from .platooning import PlatooningSim, run_platooning_simulation
from .car_following import CarFollowingSim, run_car_following_simulation
from .utils import CRRModifier, calculate_confidence_interval, append_df_to_excel, sanitize_workbook

__all__ = [
    "SimulationBase", "NetworkGenerator", "RouteGenerator",
    "PlatooningSim", "run_platooning_simulation",
    "CarFollowingSim", "run_car_following_simulation",
    "CRRModifier", "calculate_confidence_interval",
    "append_df_to_excel", "sanitize_workbook",
]
