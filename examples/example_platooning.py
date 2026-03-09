  #!/usr/bin/env python3
"""
Minimal Platooning Example

Demonstrates how to run a single platooning scenario with RTSim.
No parallel processing, no confidence intervals — just one run.

Prerequisites:
    - SUMO installed and SUMO_HOME set
    - Plexe installed (pip install plexe)
    - PHEMlight emission files generated (see tools/generate_phemlight_files.py)
    - Route template files in the expected folder structure

Usage:
    python examples/example_platooning.py
"""

import os
import sys

# Add project root to path so we can import from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core import SimulationBase, NetworkGenerator, RouteGenerator
from src.platooning import run_platooning_simulation
from src.utils import CRRModifier


def main():
    # === PATHS — Update these to match your setup ===
    xodr_file = "data/opendrive/experiment_e.xodr"
    sumo_cfg = "data/sumo/configs/grade0.sumocfg"
    route_base_dir = "data/sumo/routes/platooning"
    phem_dir = os.path.join(
        os.environ.get("SUMO_HOME", "/usr/share/sumo"), "data/emissions"
    )

    # === PARAMETERS ===
    model = "Model1"
    truck_count = 2
    min_gap = 5.0
    sigma, tau = 0.3, 0.90       # Automation level 2
    accel = 0.6
    speed_kmh = 90
    slope = 0.0
    road_type = "primary"

    print("=" * 50)
    print("RTSim — Platooning Example")
    print("=" * 50)

    # Step 1: Generate network for this slope
    print("\n[1] Generating network...")
    net_gen = NetworkGenerator("example_output/networks")
    networks = net_gen.generate_networks(xodr_file, "net", [slope])
    _, net_path = networks[0]

    # Step 2: Generate route file from template
    print("[2] Generating route file...")
    route_gen = RouteGenerator(route_base_dir, "example_output/routes")
    routes = route_gen.generate_platooning_routes(
        models=[model],
        truck_counts=[truck_count],
        min_gaps=[min_gap],
        sigma_tau_pairs=[(sigma, tau)],
        accels=[accel]
    )

    if not routes:
        print("ERROR: No route files generated. Check that template exists at:")
        print(f"  {route_base_dir}/{model}/{truck_count}truck/90/{int(min_gap)}/lower/grade01.rou.xml")
        return

    route_file = routes[0]  # Take the first (lower bound)
    print(f"  Route: {os.path.basename(route_file)}")

    # Step 3: Modify rolling resistance for road type
    print(f"[3] Setting CRR for {road_type} road...")
    crr_mod = CRRModifier(phem_dir, ".veh")
    crr_mod.modify_crr_for_routes([route_file], road_type)

    # Step 4: Run simulation
    print(f"[4] Running simulation (speed={speed_kmh} km/h)...")
    cfg_path = SimulationBase.generate_config(sumo_cfg, route_file, net_path)

    try:
        results = run_platooning_simulation(cfg_path, route_file, speed_kmh)
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

    print(f"\nScenario: {model}, {truck_count}-truck platoon, "
          f"{min_gap}m gap, sigma={sigma}, speed={speed_kmh} km/h")


if __name__ == "__main__":
    main()
