"""Vehicle Platooning and Car Following Simulation Package."""

from .core import SimulationBase, NetworkGenerator, RouteGenerator
from .platooning import PlatooningSim, run_platooning_simulation
from .car_following import CarFollowingSim, run_car_following_simulation
from .utils import CRRModifier, calculate_confidence_interval, append_df_to_excel, sanitize_workbook

__all__ = [
    # Core (shared)
    "SimulationBase",
    "NetworkGenerator",
    "RouteGenerator",
    # Platooning
    "PlatooningSim",
    "run_platooning_simulation",
    # Car Following
    "CarFollowingSim",
    "run_car_following_simulation",
    # Utils
    "CRRModifier",
    "calculate_confidence_interval",
    "append_df_to_excel",
    "sanitize_workbook",
]
