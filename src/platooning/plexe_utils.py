"""
Plexe utility functions for RTSim.

Modified from the plexe-pyapi examples (utils.py by Michele Segata).
Original: https://github.com/michele-segata/plexe-pyapi

Key modification: add_vehicle() maps each vehicle ID (v.0.0, v.0.1, ...)
to a specific vType (vtypeauto1, vtypeauto2, ...) defined in the route file.
This is how each vehicle in a platoon gets its position-specific PHEMlight
emission file with the correct drag coefficient.

    v.0.0 → vtypeauto1 → PHEMlight/.../RT_II_D_EU0.veh  (lead vehicle Cd)
    v.0.1 → vtypeauto2 → PHEMlight/.../RT_II_D_EU1.veh  (follower Cd)
    v.0.2 → vtypeauto3 → PHEMlight/.../RT_II_D_EU2.veh  (trailing Cd)

License: GNU Lesser General Public License v3.0
Copyright (c) 2018-2022 Michele Segata <segata@ccs-labs.org>
"""

import sys
import os
import random
import math

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please set the SUMO_HOME environment variable")

import sumolib
import traci
from plexe import POS_X, POS_Y, ENGINE_MODEL_REALISTIC


# Maximum supported platoon size.
# Each vehicle ID maps to a vType in the route file:
#   v.0.0 → vtypeauto1, v.0.1 → vtypeauto2, ..., v.0.6 → vtypeauto7
MAX_PLATOON_SIZE = 7


def add_vehicle(plexe, vid, position, lane, speed, vtype=None):
    """
    Add a vehicle to the simulation with position-specific vType.

    The vehicle ID determines which vType is used:
        v.0.0 → vtypeauto1 (lead vehicle)
        v.0.1 → vtypeauto2 (second vehicle)
        v.0.2 → vtypeauto3 (third vehicle)
        ...

    Each vType in the route file references a different PHEMlight emission
    file with position-specific drag coefficient from CFD analysis.
    """
    # Extract position index from vehicle ID (v.0.{index})
    parts = vid.split('.')
    if len(parts) >= 3:
        idx = int(parts[2])
    else:
        idx = 0

    vtype_id = f"vtypeauto{idx + 1}"

    if plexe.version[0] >= 1:
        traci.vehicle.add(
            vid, "platoon_route",
            departPos=str(position),
            departSpeed=str(speed),
            departLane=str(lane),
            typeID=vtype_id
        )
    else:
        traci.vehicle.add(
            vid, "platoon_route",
            pos=position,
            speed=speed,
            lane=lane,
            typeID=vtype_id
        )


def add_platooning_vehicle(plexe, vid, position, lane, speed, tau,
                           cacc_spacing, vtype=None, real_engine=False):
    """
    Add a platooning vehicle with CACC parameters configured.

    Args:
        plexe:         Plexe API instance
        vid:           Vehicle ID (e.g., 'v.0.0')
        position:      Departure position on the road (meters)
        lane:          Lane index
        speed:         Departure speed (m/s)
        tau:           ACC headway time (seconds)
        cacc_spacing:  Desired gap for CACC (meters)
        vtype:         Not used (kept for API compatibility)
        real_engine:   Use realistic engine model (default: False)
    """
    add_vehicle(plexe, vid, position, lane, speed, vtype)

    plexe.set_path_cacc_parameters(vid, cacc_spacing, 2, 1, 0.5)
    plexe.set_cc_desired_speed(vid, speed)
    plexe.set_acc_headway_time(vid, tau)

    if real_engine:
        plexe.set_engine_model(vid, ENGINE_MODEL_REALISTIC)
        plexe.set_vehicles_file(vid, "vehicles.xml")
        plexe.set_vehicle_model(vid, "alfa-147")

    traci.vehicle.setColor(vid, (
        random.uniform(0, 255),
        random.uniform(0, 255),
        random.uniform(0, 255), 255
    ))


def get_distance(plexe, v1, v2):
    """
    Returns the Euclidean distance between two vehicles.

    Args:
        plexe: Plexe API instance
        v1:    ID of first vehicle
        v2:    ID of second vehicle

    Returns:
        Distance in meters (minus 4m for vehicle length approximation)
    """
    v1_data = plexe.get_vehicle_data(v1)
    v2_data = plexe.get_vehicle_data(v2)
    return math.sqrt(
        (v1_data[POS_X] - v2_data[POS_X]) ** 2 +
        (v1_data[POS_Y] - v2_data[POS_Y]) ** 2
    ) - 4


def communicate(plexe, topology):
    """
    Perform V2V data transfer between platoon vehicles.

    Fetches position/speed data from each vehicle's leader and front
    vehicle, then passes it to the CACC algorithm so followers can
    maintain proper spacing.

    Args:
        plexe:    Plexe API instance
        topology: Dict mapping each vehicle ID to its 'leader' and 'front'
                  vehicle IDs. Example:
                  {
                      'v.0.0': {},
                      'v.0.1': {'front': 'v.0.0', 'leader': 'v.0.0'},
                      'v.0.2': {'front': 'v.0.1', 'leader': 'v.0.0'},
                  }
    """
    for vid, links in topology.items():
        if "leader" in links:
            ld = plexe.get_vehicle_data(links["leader"])
            plexe.set_leader_vehicle_data(vid, ld)
            plexe.set_leader_vehicle_fake_data(vid, ld)
        if "front" in links:
            fd = plexe.get_vehicle_data(links["front"])
            plexe.set_front_vehicle_data(vid, fd)
            distance = get_distance(plexe, vid, links["front"])
            plexe.set_front_vehicle_fake_data(vid, fd, distance)


def start_sumo(config_file, already_running, gui=True):
    """
    Start or restart SUMO with the given configuration.

    Args:
        config_file:     Path to .sumocfg file
        already_running: If True, reload config; if False, start fresh
        gui:             Use sumo-gui (True) or headless sumo (False)
    """
    arguments = ["--lanechange.duration", "3", "-c"]
    sumo_cmd = [sumolib.checkBinary('sumo-gui' if gui else 'sumo')]
    arguments.append(config_file)

    if already_running:
        traci.load(arguments)
    else:
        sumo_cmd.extend(arguments)
        traci.start(sumo_cmd)


def running(demo_mode, step, max_step):
    """
    Check whether the simulation should continue.

    Args:
        demo_mode: If True, run indefinitely
        step:      Current simulation step
        max_step:  Maximum step (used when demo_mode is False)
    """
    if demo_mode:
        return True
    return step <= max_step
