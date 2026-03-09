#!/usr/bin/env python3
"""
Minimal Car-Following Example

Demonstrates how to run a single car-following scenario with RTSim.
Car-following does NOT use Plexe — it relies on SUMO's built-in
Krauss model with sigma and tau parameters for automation levels.

Prerequisites:
    - SUMO installed and SUMO_HOME set
    - PHEMlight emission files in place
    - Route template files in the expected folder structure

Usage:
    python examples/example_car_following.py
"""

import os
import sys

# Add project root to path so we can import from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core import SimulationBase, NetworkGenerator, RouteGenerator
from src.car_following import run_car_following_simulation
from src.utils import CRRModifier


def main():
    # === PATHS — Update these to match your setup ===
    xodr_file = "data/opendrive/experiment_e.xodr"
    sumo_cfg = "data/sumo/configs/grade0.sumocfg"
    route_base_dir = "data/sumo/routes/car_following"
    phem_dir = os.path.join(
        os.environ.get("SUMO_HOME", "/usr/share/sumo"), "data/emissions"
    )

    # === PARAMETERS ===
    model = "Model1"
    truck_count = 1
    sigma, tau = 0.5, 1.00       # Automation level 0 (human driver)
    accel = 1.0
    speed_kmh = 60
    slope = 0.0
    road_type = "primary"
    seed = 42

    print("=" * 50)
    print("RTSim — Car-Following Example")
    print("=" * 50)

    # Step 1: Generate network
    print("\n[1] Generating network...")
    net_gen = NetworkGenerator("example_output/networks")
    networks = net_gen.generate_networks(xodr_file, "net", [slope])
    _, net_path = networks[0]

    # Step 2: Generate route file
    print("[2] Generating route file...")
    route_gen = RouteGenerator(route_base_dir, "example_output/routes")
    routes = route_gen.generate_car_following_routes(
        models=[model],
        truck_counts=[truck_count],
        sigma_tau_pairs=[(sigma, tau)],
        accels=[accel],
        speeds=[speed_kmh],
        min_gaps=[0]
    )

    if not routes:
        print("ERROR: No route files generated. Check that template exists at:")
        print(f"  {route_base_dir}/{model}/{truck_count}truck/lower/grade2.rou.xml")
        return

    route_file = routes[0]
    print(f"  Route: {os.path.basename(route_file)}")

    # Step 3: Modify rolling resistance for road type
    print(f"[3] Setting CRR for {road_type} road...")
    crr_mod = CRRModifier(phem_dir, ".PHEMLight.veh")
    crr_mod.modify_crr_for_routes([route_file], road_type)

    # Step 4: Run simulation
    print(f"[4] Running simulation (speed={speed_kmh} km/h, seed={seed})...")
    cfg_path = SimulationBase.generate_config(sumo_cfg, route_file, net_path)

    try:
        results = run_car_following_simulation(cfg_path, route_file, seed=seed)
    finally:
        if os.path.exists(cfg_path):
            os.remove(cfg_path)

    # Step 5: Print results
    print("\n" + "=" * 50)
    print("Results:")
    print("=" * 50)
    for r in results:
        fc = r['Fuel_L_per_100km']
        if fc:
            print(f"  {r['Vehicle']}: {fc:.2f} L/100km")
        else:
            print(f"  {r['Vehicle']}: N/A (no distance traveled)")

    print(f"\nScenario: {model}, sigma={sigma}, tau={tau}, "
          f"speed={speed_kmh} km/h, {road_type} road")


if __name__ == "__main__":
    main()
