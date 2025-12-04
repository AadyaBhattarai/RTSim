"""
Platooning simulation using Plexe CACC controller.
"""

import os
import re
import random
from typing import Dict, List, Any

import traci
from plexe import Plexe, CACC
from utils7 import add_platooning_vehicle, start_sumo, communicate


def run_platooning_simulation(cfg: str, route: str, speed: float) -> List[Dict[str, Any]]:
    """
    Run a platooning simulation.
    
    Route filename pattern:
    route_{model}_{count}truck_{variant}_minGap_{gap}_tau_{tau}_accel_{accel}_length_{length}_sigma_{sigma}.rou.xml
    """
    pat = re.compile(
        r'^route_(\w+)_(\d+)truck_(lower|upper)_minGap_([\d\.]+)_tau_([\d\.]+)'
        r'_accel_([\d\.]+)_length_([\d\.]+)_sigma_([\d\.]+)\.rou\.xml$'
    )
    m = pat.match(os.path.basename(route))
    if not m:
        raise ValueError(f"Bad route: {route}")
    
    model, n_str, variant, minGap_str, tau_str, accel_str, length_str, sigma_str = m.groups()
    n = int(n_str)
    minGap = float(minGap_str)
    tau = float(tau_str)
    accel = float(accel_str)
    length = float(length_str)
    sigma = float(sigma_str)
    
    DISTANCE = minGap
    SPEED = speed / 3.6
    VEHICLES = [f"v.0.{i}" for i in range(n)]
    
    start_sumo(cfg, False, False)
    
    plexe = Plexe()
    traci.addStepListener(plexe)
    
    step = 0
    dSPEED = SPEED + sigma * accel * traci.simulation.getDeltaT()
    
    topology = {}
    cumulative_fuel_consumption = {}
    cumulative_distance = {}
    
    for i in range(n):
        vid = f"v.0.{i}"
        depart_pos = (n - i + 1) * (DISTANCE + length)
        
        add_platooning_vehicle(
            plexe, vid, depart_pos, 0, dSPEED, tau, DISTANCE, real_engine=False
        )
        
        plexe.set_fixed_lane(vid, 0, False)
        traci.vehicle.setSpeedMode(vid, 0)
        plexe.use_controller_acceleration(vid, False)
        plexe.set_active_controller(vid, CACC)
        plexe.set_acc_headway_time(vid, tau)
        
        if i > 0:
            topology[vid] = {"front": f"v.0.{i-1}", "leader": "v.0.0"}
        else:
            topology[vid] = {}
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        if step % 10 == 1 and 'v.0.0' in traci.vehicle.getIDList():
            communicate(plexe, topology)
        
        if step % 10 == 0 and 'v.0.0' in traci.vehicle.getIDList():
            ul = SPEED - sigma * random.uniform(0, accel * traci.simulation.getDeltaT())
            for veh_id in VEHICLES:
                if veh_id in traci.vehicle.getIDList():
                    traci.vehicle.setSpeed(veh_id, ul)
        
        vehicle_ids = traci.vehicle.getIDList()
        for veh_id in vehicle_ids:
            if veh_id not in cumulative_fuel_consumption:
                cumulative_fuel_consumption[veh_id] = 0.0
                cumulative_distance[veh_id] = 0.0
            
            fuel = traci.vehicle.getFuelConsumption(veh_id) * traci.simulation.getDeltaT()
            distance_km = traci.vehicle.getDistance(veh_id) / 1000
            
            if distance_km > 0:
                cumulative_fuel_consumption[veh_id] += fuel
                cumulative_distance[veh_id] = distance_km
        
        step += 1
    
    traci.close()
    
    results = []
    for veh_id in cumulative_fuel_consumption:
        km = cumulative_distance.get(veh_id, 0.0)
        fuel_L100km = (cumulative_fuel_consumption[veh_id] / 850000.0 / km * 100) if km > 0 else None
        
        results.append({
            'Scenario': 'platooning',
            'Model': model,
            'Count': n,
            'minGap': minGap,
            'Tau': tau,
            'Accel': accel,
            'Sigma': sigma,
            'Speed': speed,
            'Vehicle': veh_id,
            'Fuel_L_per_100km': fuel_L100km,
            'Distance_km': km
        })
    
    return results
