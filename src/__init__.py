"""
Vehicle Platooning Simulation Package

A modular framework for simulating vehicle platooning and car-following
scenarios using SUMO and Plexe.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .core import SimulationBase, NetworkGenerator, RouteGenerator
from .platooning import PlatooningSim, PlatoonController
from .car_following import CarFollowingSim
from .utils import ConfigLoader, ExcelWriter, CRRModifier, Statistics

__all__ = [
    "SimulationBase",
    "NetworkGenerator",
    "RouteGenerator",
    "PlatooningSim",
    "PlatoonController",
    "CarFollowingSim",
    "ConfigLoader",
    "ExcelWriter",
    "CRRModifier",
    "Statistics",
]
