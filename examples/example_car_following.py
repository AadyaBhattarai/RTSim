#!/usr/bin/env python3
"""
Example: Running a Car Following Simulation

This example shows how to use the modules to run a car following simulation.
Car following does NOT use Plexe - it uses SUMO's built-in car following model.

Prerequisites:
- SUMO installed and SUMO_HOME set
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import our modules
from core import SimulationBase, NetworkGenerator, RouteGenerator
from car_following import run_car_following_simulation
from utils import CRRModifier, append_df_to_excel, sanitize_workbook

import pandas as pd


def main():
    # =========================================================================
    # CONFIGURATION - Modify these paths to match your setup
    # =========================================================================
    
    # Your OpenDRIVE file
    xodr_file = "experiment_e.xodr"
    
    # Your base SUMO config file
    sumo_cfg = "grade0.sumocfg"
    
    # Your car following route templates folder
    # Structure: carfollowing/Model1/1truck/lower/grade2.rou.xml
    route_base_dir = "examples/carfollowing"
    
    # Your emissions folder
    # Car following uses "Single" subfolder: PHEMlight/Model1/Single/90/Lower/
    phem_dir = "examples/PHEMlight"
    
    # Output directory
    output_dir = "car_following_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # =========================================================================
    # PARAMETERS
    # =========================================================================
    
    models = ["Model4", "Model5"]
    truck_counts = [1]                         # Single truck for car following
    sigma_tau_pairs = [(0.5, 1.0), (0.0, 0.8)]
    accel_values = [0.2, 0.6]
    speeds_km_h = [60, 90]
    min_gaps = [5, 10]
    slope_values = [0.0, 0.08]
    road_type = "cross_country"
    trials = 5
    
    crr_values = {
        'primary': 0.006923,
        'secondary': 0.010,
        'cross_country': 0.025
    }
    
    # =========================================================================
    # STEP 1: Generate Networks
    # =========================================================================
    
    print("=" * 60)
    print("STEP 1: Generating networks")
    print("=" * 60)
    
    net_gen = NetworkGenerator(os.path.join(output_dir, "networks"))
    networks = net_gen.generate_networks(xodr_file, "network", slope_values)
    
    # =========================================================================
    # STEP 2: Generate Route Files
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("STEP 2: Generating route files")
    print("=" * 60)
    
    route_gen = RouteGenerator(route_base_dir, os.path.join(output_dir, "routes"))
    route_files = route_gen.generate_car_following_routes(
        models=models,
        truck_counts=truck_counts,
        sigma_tau_pairs=sigma_tau_pairs,
        accels=accel_values,
        speeds=speeds_km_h,
        min_gaps=min_gaps
    )
    
    print(f"  Generated {len(route_files)} route files")
    
    # =========================================================================
    # STEP 3: Modify CRR (using .PHEMLight.veh suffix for car following)
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("STEP 3: Modifying CRR values")
    print("=" * 60)
    
    crr_modifier = CRRModifier(phem_dir, ".PHEMLight.veh")
    crr_modifier.modify_crr_for_routes(route_files, road_type, crr_values)
    
    # =========================================================================
    # STEP 4: Run Simulations
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("STEP 4: Running simulations")
    print("=" * 60)
    
    all_results = []
    
    for slope, net_path in networks:
        for route_file in route_files:
            for trial in range(1, trials + 1):
                print(f"\n  Running: slope={slope}, trial={trial}")
                print(f"    Route: {os.path.basename(route_file)}")
                
                try:
                    # Generate config
                    cfg_path = SimulationBase.generate_config(
                        sumo_cfg, route_file, net_path, unique=True
                    )
                    
                    # Run simulation (trial is used as seed for randomization)
                    results = run_car_following_simulation(cfg_path, route_file, seed=trial)
                    
                    # Add metadata
                    for r in results:
                        r['Slope'] = slope
                        r['RoadType'] = road_type
                        r['Trial'] = trial
                    
                    all_results.extend(results)
                    
                    # Print results
                    for r in results:
                        print(f"    Vehicle {r['Vehicle']}: {r['Fuel_L_per_100km']:.2f} L/100km")
                    
                    # Cleanup
                    if os.path.exists(cfg_path):
                        os.remove(cfg_path)
                        
                except Exception as e:
                    print(f"    ERROR: {e}")
    
    # =========================================================================
    # STEP 5: Save Results
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("STEP 5: Saving results")
    print("=" * 60)
    
    if all_results:
        df = pd.DataFrame(all_results)
        output_file = os.path.join(output_dir, "car_following_results.xlsx")
        sanitize_workbook(output_file)
        append_df_to_excel(df, output_file, "Results")
        print(f"  Saved to: {output_file}")
    
    print("\nDONE!")


if __name__ == "__main__":
    main()
